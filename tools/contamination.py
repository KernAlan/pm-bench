#!/usr/bin/env python3
"""
tools/contamination.py — Contamination / memorization analysis for PM-Bench.

For each MCQ scenario, generates a *paraphrased variant* by asking an LLM
to:

  1. Rewrite the trigger in different words (same meaning, same facts).
  2. Shuffle the A/B/C/D order (and track which new letter corresponds to
     the ORIGINAL correct answer).
  3. Keep the workspace files identical.

Then we evaluate the same subject model on the original vs. paraphrased
versions. A large accuracy drop on paraphrased items indicates the model
may have memorized the original phrasing rather than reasoned about the
content. A small or zero drop is evidence that performance reflects
genuine capability.

Outputs
-------
  analysis/contamination_report.md
      - Per-model original vs. paraphrased accuracy
      - Delta (original - paraphrased) per model
      - Flagged items where the model got the original right but missed
        the paraphrase (the clearest memorization signal)
      - Per-scenario drill-down for items with delta > 20% across models

Usage
-----
    python tools/contamination.py --model claude-sonnet-4-20250514 \\
        --n-scenarios 20

    # Use a separate paraphraser model:
    python tools/contamination.py --model gpt-4o --provider openai \\
        --paraphraser-model claude-sonnet-4-20250514 \\
        --paraphraser-provider anthropic

    # Default sample = Superhuman PM Judgment (20 items).
    python tools/contamination.py --model gpt-4o --provider openai

Dependencies
------------
  anthropic, openai (depending on which providers you use)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SCENARIOS_FILE = ROOT / "scenarios" / "scenarios.json"
ANALYSIS_DIR = ROOT / "analysis"

try:
    from run import (  # type: ignore
        MCQ_SYSTEM,
        build_context,
        build_messages,
        dispatch,
        extract_mcq_choice,
        load_scenarios,
    )
except Exception as e:
    print(f"Could not import helpers from run.py: {e}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# API-key guard
# ---------------------------------------------------------------------------

def check_keys(providers: set[str]) -> bool:
    ok = True
    if "anthropic" in providers and not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set.", file=sys.stderr)
        ok = False
    if "openai" in providers and not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set.", file=sys.stderr)
        ok = False
    return ok


# ---------------------------------------------------------------------------
# Paraphrase generation
# ---------------------------------------------------------------------------

PARAPHRASE_SYSTEM = (
    "You rewrite multiple-choice questions to test whether a model has "
    "truly understood the content rather than memorized the surface form. "
    "You must preserve every fact and the correctness of the intended "
    "answer. You must output strict JSON."
)

PARAPHRASE_TEMPLATE = """You are given a multiple-choice question. Rewrite it by:

1. Paraphrasing the trigger/question in different words (same meaning, same
   facts, natural tone). Do not change numbers, names, or substantive content.
2. Rewriting each option's text in different words (preserve meaning).
3. Shuffling the A/B/C/D order with a non-trivial permutation (not identity).
4. Reporting which NEW letter corresponds to the ORIGINAL correct answer.

Original trigger (includes the options):
<trigger>
{trigger}
</trigger>

Original correct answer: {correct}

Return STRICT JSON (no prose, no markdown fences) with this schema:
{{
  "paraphrased_trigger": "the rewritten question AND options, formatted the same way",
  "new_correct_letter": "A" | "B" | "C" | "D",
  "mapping": {{ "A": "new_letter_for_old_A", "B": "...", "C": "...", "D": "..." }}
}}
"""


def strip_json_fences(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    return t.strip()


def paraphrase_scenario(scenario: dict, provider: str, model: str) -> dict | None:
    trigger = scenario.get("trigger", "")
    correct = (scenario.get("correct_answer") or "").strip().upper()
    if correct not in ("A", "B", "C", "D"):
        return None
    prompt = PARAPHRASE_TEMPLATE.format(trigger=trigger, correct=correct)
    messages = [
        {"role": "system", "content": PARAPHRASE_SYSTEM},
        {"role": "user", "content": prompt},
    ]
    try:
        resp = dispatch(provider, messages, model, max_tokens=1500)
    except Exception as e:
        print(f"    [paraphrase error] {e}", file=sys.stderr)
        return None
    text = strip_json_fences(resp.get("text", ""))
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Sometimes models wrap in extra text — try to extract a JSON object.
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            print(f"    [paraphrase error] non-JSON response", file=sys.stderr)
            return None
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None

    new_trigger = data.get("paraphrased_trigger", "").strip()
    new_correct = (data.get("new_correct_letter") or "").strip().upper()
    if not new_trigger or new_correct not in ("A", "B", "C", "D"):
        return None
    return {
        "paraphrased_trigger": new_trigger,
        "new_correct_letter": new_correct,
        "mapping": data.get("mapping") or {},
    }


# ---------------------------------------------------------------------------
# Subject-model evaluation
# ---------------------------------------------------------------------------

def evaluate(scenario: dict, trigger: str, correct: str,
             provider: str, model: str) -> dict:
    """Run one scenario (with possibly overridden trigger) and return
    {chosen, correct, response_text}."""
    sub = dict(scenario)
    sub["trigger"] = trigger
    context = build_context(sub)
    messages = build_messages(sub, context, MCQ_SYSTEM)
    try:
        response = dispatch(provider, messages, model, max_tokens=1024)
    except Exception as e:
        return {"chosen": None, "correct": False, "response_text": "",
                "error": str(e)}
    chosen = extract_mcq_choice(response.get("text", ""))
    return {
        "chosen": chosen,
        "correct": chosen == correct,
        "response_text": response.get("text", ""),
    }


# ---------------------------------------------------------------------------
# Sample selection
# ---------------------------------------------------------------------------

def select_sample(all_scenarios: list[dict], n: int) -> list[dict]:
    """Default: Superhuman PM Judgment (20 items). If fewer exist,
    pad with other MCQ scenarios. If n != 20, take the first N MCQ items
    from Superhuman first, then general MCQ."""
    mcq = [s for s in all_scenarios if s.get("scoring") == "mcq"]
    superhuman = [s for s in mcq if s.get("category") == "Superhuman PM Judgment"]
    other = [s for s in mcq if s.get("category") != "Superhuman PM Judgment"]
    ordered = superhuman + other
    return ordered[:n]


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(path: Path, model: str, paraphraser: str,
                 records: list[dict], failed_paraphrase: list[int]) -> None:
    lines: list[str] = []
    lines.append("# PM-Bench Contamination Report")
    lines.append("")
    lines.append(f"- Subject model: `{model}`")
    lines.append(f"- Paraphraser model: `{paraphraser}`")
    lines.append(f"- Scenarios evaluated: {len(records)}")
    if failed_paraphrase:
        lines.append(f"- Scenarios where paraphrase generation failed: "
                     f"{len(failed_paraphrase)} (ids: {failed_paraphrase})")
    lines.append("")

    if not records:
        lines.append("_No usable paraphrased items._")
        path.write_text("\n".join(lines), encoding="utf-8")
        return

    orig_correct = sum(1 for r in records if r["orig_correct"])
    para_correct = sum(1 for r in records if r["para_correct"])
    n = len(records)
    orig_acc = orig_correct / n
    para_acc = para_correct / n
    delta = orig_acc - para_acc

    lines.append("## Summary")
    lines.append("")
    lines.append("| metric | value |")
    lines.append("|---|---|")
    lines.append(f"| Original accuracy | {orig_acc:.3f} ({orig_correct}/{n}) |")
    lines.append(f"| Paraphrased accuracy | {para_acc:.3f} ({para_correct}/{n}) |")
    lines.append(f"| Delta (original − paraphrased) | {delta:+.3f} |")
    lines.append("")
    if abs(delta) > 0.20:
        lines.append(f"> **Flagged: absolute delta {abs(delta):.2f} exceeds "
                     f"the 20% threshold.** This may indicate memorization "
                     f"of the original phrasing.")
    else:
        lines.append(f"> Delta within normal range (|delta| <= 0.20). No "
                     f"strong contamination signal.")
    lines.append("")

    # Per-item table.
    lines.append("## Per-item results")
    lines.append("")
    lines.append("| id | name | original | paraphrased | flagged |")
    lines.append("|---|---|---|---|---|")
    flagged: list[dict] = []
    for r in records:
        orig = "PASS" if r["orig_correct"] else "FAIL"
        para = "PASS" if r["para_correct"] else "FAIL"
        # Flag individual items: original right but paraphrase wrong.
        item_flag = r["orig_correct"] and not r["para_correct"]
        mark = "YES" if item_flag else ""
        if item_flag:
            flagged.append(r)
        lines.append(f"| {r['id']} | {r['name']} | {orig} | {para} | {mark} |")
    lines.append("")

    lines.append(f"## Flagged items — correct on original, wrong on paraphrase "
                 f"({len(flagged)})")
    lines.append("")
    if not flagged:
        lines.append("_None._")
    else:
        lines.append("These are the clearest single-item memorization signals. "
                     "Review the model's reasoning on each.")
        lines.append("")
        for r in flagged:
            lines.append(f"### #{r['id']} — {r['name']}")
            lines.append("")
            lines.append(f"- Authored correct letter: **{r['authored_correct']}**")
            lines.append(f"- Paraphrase correct letter: **{r['para_correct_letter']}**")
            lines.append(f"- Original chosen: {r['orig_chosen']}")
            lines.append(f"- Paraphrased chosen: {r['para_chosen']}")
            lines.append("")
            lines.append("**Paraphrased trigger:**")
            lines.append("")
            lines.append("```")
            lines.append(r["paraphrased_trigger"])
            lines.append("```")
            lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Contamination / memorization check via paraphrased triggers.")
    parser.add_argument("--model", required=True,
                        help="Subject model to evaluate.")
    parser.add_argument("--provider", choices=["anthropic", "openai"],
                        default="anthropic",
                        help="Provider for the subject model.")
    parser.add_argument("--paraphraser-model", default=None,
                        help="Model used to generate paraphrases. Defaults "
                             "to the subject model (but using a DIFFERENT "
                             "model is recommended).")
    parser.add_argument("--paraphraser-provider", choices=["anthropic", "openai"],
                        default=None,
                        help="Provider for the paraphraser model.")
    parser.add_argument("--n-scenarios", type=int, default=20,
                        help="Number of scenarios to sample (default: 20).")
    parser.add_argument("--sleep", type=float, default=0.5,
                        help="Seconds to sleep between API calls.")
    args = parser.parse_args()

    paraphraser_model = args.paraphraser_model or args.model
    paraphraser_provider = args.paraphraser_provider or args.provider

    if not check_keys({args.provider, paraphraser_provider}):
        sys.exit(1)

    all_scenarios = load_scenarios(SCENARIOS_FILE)
    sample = select_sample(all_scenarios, args.n_scenarios)
    if not sample:
        print("No MCQ scenarios available.", file=sys.stderr)
        sys.exit(1)

    print(f"Subject: {args.provider}/{args.model}")
    print(f"Paraphraser: {paraphraser_provider}/{paraphraser_model}")
    print(f"Scenarios: {len(sample)}\n")

    records: list[dict] = []
    failed_paraphrase: list[int] = []

    for i, scenario in enumerate(sample, 1):
        sid = scenario["id"]
        name = scenario.get("name", str(sid))
        authored = (scenario.get("correct_answer") or "").strip().upper()
        print(f"[{i}/{len(sample)}] #{sid} {name}")

        para = paraphrase_scenario(scenario, paraphraser_provider, paraphraser_model)
        if para is None:
            print("    (paraphrase failed — skipping)")
            failed_paraphrase.append(sid)
            if i < len(sample):
                time.sleep(args.sleep)
            continue

        # Original.
        orig_res = evaluate(scenario, scenario["trigger"], authored,
                            args.provider, args.model)
        # Paraphrased.
        para_res = evaluate(scenario, para["paraphrased_trigger"],
                            para["new_correct_letter"],
                            args.provider, args.model)

        print(f"    original   chosen={orig_res['chosen']} "
              f"(expected={authored})  -> "
              f"{'PASS' if orig_res['correct'] else 'FAIL'}")
        print(f"    paraphrase chosen={para_res['chosen']} "
              f"(expected={para['new_correct_letter']})  -> "
              f"{'PASS' if para_res['correct'] else 'FAIL'}")

        records.append({
            "id": sid,
            "name": name,
            "authored_correct": authored,
            "para_correct_letter": para["new_correct_letter"],
            "paraphrased_trigger": para["paraphrased_trigger"],
            "orig_chosen": orig_res["chosen"],
            "para_chosen": para_res["chosen"],
            "orig_correct": orig_res["correct"],
            "para_correct": para_res["correct"],
        })

        if i < len(sample):
            time.sleep(args.sleep)

    ANALYSIS_DIR.mkdir(exist_ok=True)
    report_path = ANALYSIS_DIR / "contamination_report.md"
    write_report(report_path, args.model, paraphraser_model, records,
                 failed_paraphrase)
    print(f"\nWrote {report_path}")


if __name__ == "__main__":
    main()
