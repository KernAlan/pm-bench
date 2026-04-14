#!/usr/bin/env python3
"""
tools/validate_answers.py — Multi-model answer-key validation for PM-Bench.

Uses N language models as independent "expert annotators" to cross-validate
the authored `correct_answer` in `scenarios/scenarios.json`. Only MCQ
scenarios are validated (keyword and tool_use scoring types are skipped,
since they are not multiple-choice).

For each MCQ scenario we:
  1. Present the workspace context + trigger to each annotator model
     (the authored correct answer is NEVER shown).
  2. Record each model's chosen letter (A/B/C/D).
  3. Compute inter-annotator agreement:
       - agreement_fraction: share of annotators matching the authored key
       - majority vote across annotators
       - Fleiss' kappa across annotators (one value per scenario when
         >= 2 annotators are available, reported globally)
  4. Flag scenarios where the majority of annotators disagree with the
     authored answer — these are candidates for the authors to review.

Outputs
-------
  analysis/answer_validation.csv
      id, name, category, authored_answer, <one column per model>,
      agreement_fraction, majority_vote, disputed

  analysis/disputed_items.md
      Human-readable list of disputed items with the question text and
      each annotator's answer, so authors can review and correct.

Usage
-----
    # Same provider for all models:
    python tools/validate_answers.py \\
        --models claude-sonnet-4-20250514 claude-opus-4-5-20250929 \\
        --provider anthropic

    # Mixed providers:
    python tools/validate_answers.py \\
        --models claude-sonnet-4-20250514 gpt-4o \\
        --provider-map 'claude-sonnet-4-20250514:anthropic,gpt-4o:openai'

    # Subset (for quick testing):
    python tools/validate_answers.py --models gpt-4o --provider openai \\
        --limit 5

Dependencies
------------
  anthropic, openai (whichever providers you use)
  pandas (optional — falls back to plain CSV writer if unavailable)
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # so we can import run.py

SCENARIOS_FILE = ROOT / "scenarios" / "scenarios.json"
ANALYSIS_DIR = ROOT / "analysis"

# Re-use the runner's helpers so context assembly and MCQ extraction are
# byte-for-byte identical to the main benchmark.
try:
    from run import (  # type: ignore
        MCQ_SYSTEM,
        build_context,
        build_messages,
        extract_mcq_choice,
        load_scenarios,
    )
except Exception as e:  # pragma: no cover — surfaced to the user.
    print(f"Could not import helpers from run.py: {e}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Provider dispatch with graceful missing-key handling
# ---------------------------------------------------------------------------

def _ensure_anthropic():
    try:
        from anthropic import Anthropic  # type: ignore
    except ImportError:
        print("Install anthropic:  pip install anthropic", file=sys.stderr)
        sys.exit(1)
    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set — skipping Anthropic models.",
              file=sys.stderr)
        return None
    return Anthropic()


def _ensure_openai():
    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        print("Install openai:  pip install openai", file=sys.stderr)
        sys.exit(1)
    import os
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set — skipping OpenAI models.",
              file=sys.stderr)
        return None
    return OpenAI()


def call_model(provider: str, client: Any, messages: list[dict],
               model: str, max_tokens: int = 512) -> str:
    """Return the text response, or '' on failure."""
    if client is None:
        return ""
    try:
        if provider == "anthropic":
            system_text = ""
            chat = []
            for m in messages:
                if m["role"] == "system":
                    system_text += m["content"] + "\n"
                else:
                    chat.append(m)
            kwargs: dict[str, Any] = dict(model=model, max_tokens=max_tokens,
                                          messages=chat)
            if system_text.strip():
                kwargs["system"] = system_text.strip()
            resp = client.messages.create(**kwargs)
            parts = [b.text for b in resp.content if b.type == "text"]
            return "\n".join(parts)
        else:
            resp = client.chat.completions.create(
                model=model, messages=messages, max_tokens=max_tokens)
            return resp.choices[0].message.content or ""
    except Exception as e:
        print(f"    [error] {provider}/{model}: {e}", file=sys.stderr)
        return ""


# ---------------------------------------------------------------------------
# Fleiss' kappa (multi-annotator agreement)
# ---------------------------------------------------------------------------

def fleiss_kappa(annotations: list[list[str]], categories: list[str]) -> float:
    """`annotations[i]` is the list of annotator answers for item i.
    Each annotator contributes at most once per item. Missing answers are
    skipped. Returns NaN if insufficient data.

    Implements the standard Fleiss formulation, tolerating a variable
    number of raters per item by normalizing each row.
    """
    if not annotations:
        return float("nan")
    N = len(annotations)
    k = len(categories)
    if k < 2 or N < 2:
        return float("nan")

    # Per-item proportions.
    P_i: list[float] = []
    marginals = {c: 0 for c in categories}
    total_ratings = 0
    for row in annotations:
        clean = [a for a in row if a in categories]
        n_i = len(clean)
        if n_i < 2:
            # An item with 1 rater has no agreement info; skip.
            continue
        counts = Counter(clean)
        for c in categories:
            marginals[c] += counts.get(c, 0)
        total_ratings += n_i
        # Agreement for this item.
        s = sum(counts.get(c, 0) * (counts.get(c, 0) - 1) for c in categories)
        P_i.append(s / (n_i * (n_i - 1)))

    if not P_i or total_ratings == 0:
        return float("nan")
    P_bar = sum(P_i) / len(P_i)
    p_j = {c: marginals[c] / total_ratings for c in categories}
    P_e = sum(p_j[c] ** 2 for c in categories)
    if P_e >= 1.0:
        return float("nan")
    return (P_bar - P_e) / (1.0 - P_e)


# ---------------------------------------------------------------------------
# CLI parsing
# ---------------------------------------------------------------------------

def parse_provider_map(s: str | None, models: list[str],
                        default_provider: str) -> dict[str, str]:
    if not s:
        return {m: default_provider for m in models}
    out: dict[str, str] = {}
    for chunk in s.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ":" not in chunk:
            raise SystemExit(f"--provider-map entry must be 'model:provider', "
                             f"got: {chunk!r}")
        m, p = chunk.split(":", 1)
        out[m.strip()] = p.strip()
    for m in models:
        out.setdefault(m, default_provider)
    return out


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def annotate_scenario(scenario: dict, models: list[str],
                      providers: dict[str, str],
                      clients: dict[str, Any]) -> dict[str, str | None]:
    """Return {model_name: chosen_letter_or_None} for one scenario."""
    context = build_context(scenario)
    messages = build_messages(scenario, context, MCQ_SYSTEM)
    answers: dict[str, str | None] = {}
    for model in models:
        provider = providers[model]
        client = clients.get(provider)
        if client is None:
            answers[model] = None
            continue
        text = call_model(provider, client, messages, model)
        answers[model] = extract_mcq_choice(text) if text else None
    return answers


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_disputed(path: Path, disputed: list[dict], models: list[str]) -> None:
    lines: list[str] = []
    lines.append("# Disputed Items — Majority of Annotators Disagree with Authored Answer")
    lines.append("")
    lines.append("Each item below was answered by the annotator models listed. "
                 "The *majority vote* of the annotators differs from the "
                 "authored `correct_answer`. Review these items and decide "
                 "whether the key should be corrected or the question "
                 "clarified.")
    lines.append("")
    if not disputed:
        lines.append("_No disputed items detected._")
        path.write_text("\n".join(lines), encoding="utf-8")
        return

    for item in disputed:
        lines.append(f"## #{item['id']} — {item['name']}  ({item['category']})")
        lines.append("")
        lines.append(f"- **Authored answer:** {item['authored_answer']}")
        lines.append(f"- **Majority vote:** {item['majority_vote']}")
        lines.append(f"- **Agreement fraction (w/ authored):** "
                     f"{item['agreement_fraction']:.2f}")
        lines.append("")
        lines.append("**Annotator answers:**")
        lines.append("")
        for m in models:
            ans = item.get(m) or "(no answer)"
            lines.append(f"- `{m}`: {ans}")
        lines.append("")
        lines.append("**Trigger / question:**")
        lines.append("")
        lines.append("```")
        lines.append(item["trigger"])
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate authored MCQ answer keys using multiple LLM annotators.")
    parser.add_argument("--models", nargs="+", required=True,
                        help="Model names to use as annotators.")
    parser.add_argument("--provider", choices=["anthropic", "openai"],
                        default="anthropic",
                        help="Default provider for all models "
                             "(overridden by --provider-map).")
    parser.add_argument("--provider-map", type=str, default=None,
                        help="Comma-separated model:provider pairs "
                             "(e.g. 'gpt-4o:openai,claude-sonnet-4-20250514:anthropic').")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit to first N MCQ scenarios (for testing).")
    parser.add_argument("--sleep", type=float, default=0.4,
                        help="Seconds to sleep between scenarios.")
    args = parser.parse_args()

    providers = parse_provider_map(args.provider_map, args.models, args.provider)

    # Build client per provider, once. Missing-key: graceful skip.
    clients: dict[str, Any] = {}
    if any(p == "anthropic" for p in providers.values()):
        clients["anthropic"] = _ensure_anthropic()
    if any(p == "openai" for p in providers.values()):
        clients["openai"] = _ensure_openai()

    usable = [m for m in args.models if clients.get(providers[m]) is not None]
    if not usable:
        print("No usable models (missing API keys). Exiting.", file=sys.stderr)
        sys.exit(1)
    if len(usable) != len(args.models):
        skipped = set(args.models) - set(usable)
        print(f"Skipping models with no API key: {sorted(skipped)}")

    all_scenarios = load_scenarios(SCENARIOS_FILE)
    mcq = [s for s in all_scenarios if s.get("scoring") == "mcq"]
    if args.limit:
        mcq = mcq[:args.limit]
    print(f"Validating {len(mcq)} MCQ scenario(s) with "
          f"{len(usable)} annotator(s): {usable}\n")

    rows: list[dict] = []
    disputed: list[dict] = []
    annotations_for_kappa: list[list[str]] = []

    for i, scenario in enumerate(mcq, 1):
        sid = scenario["id"]
        name = scenario.get("name", str(sid))
        authored = (scenario.get("correct_answer") or "").strip().upper()
        print(f"[{i}/{len(mcq)}] #{sid} {name}")
        answers = annotate_scenario(scenario, usable, providers, clients)
        for m, a in answers.items():
            print(f"    {m}: {a}  (authored: {authored})")

        voted = [a for a in answers.values() if a in ("A", "B", "C", "D")]
        annotations_for_kappa.append(voted)

        n = len(voted)
        agree = sum(1 for a in voted if a == authored)
        frac = (agree / n) if n else float("nan")

        if voted:
            counts = Counter(voted)
            top_count = max(counts.values())
            # Ties broken alphabetically for determinism.
            majority = sorted(
                [c for c, k in counts.items() if k == top_count]
            )[0]
        else:
            majority = None

        disputed_flag = (majority is not None
                         and majority != authored
                         and n >= 2
                         and counts[majority] > n / 2)

        row: dict[str, Any] = {
            "id": sid,
            "name": name,
            "category": scenario.get("category", ""),
            "authored_answer": authored,
            "agreement_fraction": round(frac, 4) if not math.isnan(frac) else "",
            "majority_vote": majority or "",
            "disputed": disputed_flag,
        }
        for m in args.models:
            row[m] = answers.get(m) or ""
        rows.append(row)

        if disputed_flag:
            disp = dict(row)
            disp["trigger"] = scenario.get("trigger", "")
            disputed.append(disp)

        if i < len(mcq):
            time.sleep(args.sleep)

    kappa = fleiss_kappa(annotations_for_kappa, ["A", "B", "C", "D"])
    print()
    print(f"Fleiss' kappa across annotators: "
          f"{kappa if not math.isnan(kappa) else 'NaN (insufficient data)'}")

    ANALYSIS_DIR.mkdir(exist_ok=True)
    csv_path = ANALYSIS_DIR / "answer_validation.csv"
    fieldnames = ["id", "name", "category", "authored_answer"] + list(args.models) + \
                 ["agreement_fraction", "majority_vote", "disputed"]
    write_csv(csv_path, rows, fieldnames)
    print(f"Wrote {csv_path}")

    disputed_path = ANALYSIS_DIR / "disputed_items.md"
    # Append global kappa to top of disputed report via a one-line note.
    write_disputed(disputed_path, disputed, args.models)
    # Insert kappa note after the heading.
    try:
        text = disputed_path.read_text(encoding="utf-8")
        kappa_note = (f"_Fleiss' kappa across annotators: "
                      f"**{kappa:.3f}**_" if not math.isnan(kappa)
                      else "_Fleiss' kappa: insufficient data._")
        text = text.replace(
            "# Disputed Items — Majority of Annotators Disagree with Authored Answer",
            "# Disputed Items — Majority of Annotators Disagree with Authored Answer"
            f"\n\n{kappa_note}",
            1,
        )
        disputed_path.write_text(text, encoding="utf-8")
    except Exception:
        pass

    print(f"Wrote {disputed_path}")
    print(f"\nSummary: {len(disputed)} disputed item(s) out of {len(mcq)} MCQ scenarios.")


if __name__ == "__main__":
    main()
