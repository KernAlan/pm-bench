#!/usr/bin/env python3
"""Post-run report generator for PM-Bench.

Takes a single `results/*.json` file and produces a markdown report with:
- Run metadata (timestamp, provider, model, mode, total count).
- Overall accuracy plus a per-category breakdown.
- ASCII bar charts for per-category accuracy (no matplotlib dependency,
  so the report renders the same everywhere).
- Pass / fail lists with actionable detail:
    - MCQ failures: chosen vs expected letter, response preview.
    - Keyword failures: which keyword was missing, response preview.
    - Open-ended failures: missing must_mentions, triggered red flags,
      judge verdict + evidence.

The report is written to ``results/<prefix>_report.md`` (same prefix as
the input JSON, with `.json` replaced by `_report.md`) and also echoed
to stdout so it composes well in CI logs.

Usage:
    python tools/report.py results/20260414-120000_mcq_anthropic_claude-sonnet-4.json
    python tools/report.py --stdout-only results/foo.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Pass / fail markers. These render nicely on GitHub and any UTF-8 terminal.
# When writing the file we always use UTF-8, so authoring tools see them
# correctly; stdout rendering on legacy Windows codepages will show mojibake,
# but the on-disk report is the source of truth.
PASS_MARK = "\u2713"  # check mark
FAIL_MARK = "\u2717"  # ballot x


def _load_results(path: Path) -> dict:
    if not path.exists():
        print(f"error: results file not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"error: could not parse JSON from {path}: {e}", file=sys.stderr)
        sys.exit(2)


def _category_breakdown(scenarios: list[dict]) -> dict[str, tuple[int, int]]:
    """Return {category: (correct, total)} preserving first-seen order."""
    out: dict[str, list[int]] = {}
    for s in scenarios:
        cat = s.get("category", "?")
        if cat not in out:
            out[cat] = [0, 0]
        out[cat][1] += 1
        if s.get("correct"):
            out[cat][0] += 1
    return {k: (v[0], v[1]) for k, v in out.items()}


def _ascii_bar(pct: float, width: int = 30) -> str:
    """Return a fixed-width ASCII bar for the given percentage (0-100)."""
    pct = max(0.0, min(100.0, pct))
    filled = int(round(pct / 100.0 * width))
    return "#" * filled + "-" * (width - filled)


def _preview(text: str | None, limit: int = 200) -> str:
    if not text:
        return "(empty)"
    t = text.replace("\n", " ").replace("\r", " ").strip()
    return t if len(t) <= limit else t[:limit].rstrip() + "..."


def _format_metadata(data: dict) -> list[str]:
    lines = [
        "## Run metadata",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Timestamp | `{data.get('timestamp', '?')}` |",
        f"| Mode | `{data.get('mode', '?')}` |",
        f"| Provider | `{data.get('provider', '?')}` |",
        f"| Model | `{data.get('model', '?')}` |",
        f"| Total scenarios | {data.get('total', len(data.get('scenarios', [])))} |",
        f"| Correct | {data.get('correct', 0)} |",
    ]
    iters = data.get("iterations") or data.get("iteration")
    if iters is not None:
        lines.append(f"| Iteration(s) | {iters} |")
    lines.append("")
    return lines


def _format_overall(scenarios: list[dict]) -> list[str]:
    total = len(scenarios)
    correct = sum(1 for s in scenarios if s.get("correct"))
    pct = (correct / total * 100) if total else 0.0
    return [
        "## Overall accuracy",
        "",
        f"**{correct} / {total}  ({pct:.1f}%)**",
        "",
        "```",
        f"{_ascii_bar(pct)} {pct:5.1f}%",
        "```",
        "",
    ]


def _format_categories(scenarios: list[dict]) -> list[str]:
    breakdown = _category_breakdown(scenarios)
    if not breakdown:
        return []
    max_cat_len = max(len(c) for c in breakdown)
    cat_col = max(max_cat_len, 8)
    lines = [
        "## Per-category accuracy",
        "",
        "| Category | Score | Pct | Bar |",
        "|---|---|---|---|",
    ]
    # Markdown table for machine readability.
    for cat, (c, n) in breakdown.items():
        pct = (c / n * 100) if n else 0.0
        lines.append(f"| {cat} | {c}/{n} | {pct:.1f}% | `{_ascii_bar(pct, 20)}` |")
    lines.append("")
    # ASCII chart block for terminal-native viewing.
    lines.append("```")
    lines.append(f"{'Category':<{cat_col}}  {'Score':>7}  {'Pct':>6}  Bar")
    lines.append("-" * (cat_col + 7 + 6 + 32 + 6))
    for cat, (c, n) in breakdown.items():
        pct = (c / n * 100) if n else 0.0
        lines.append(
            f"{cat:<{cat_col}}  {c:>3}/{n:<3}  {pct:>5.1f}%  {_ascii_bar(pct)}"
        )
    lines.append("```")
    lines.append("")
    return lines


def _format_failure(s: dict) -> list[str]:
    """Build the per-scenario failure detail block.

    Branches on the scoring shape we find. We prefer the richer data in
    `score_detail` when present, and fall back to top-level fields for
    older result files.
    """
    sid = s.get("id", "?")
    name = s.get("name", "?")
    cat = s.get("category", "?")
    scoring = s.get("scoring", "?")
    detail = s.get("score_detail") or {}
    head = f"#### {FAIL_MARK} #{sid} `{name}` — *{cat}* ({scoring})"
    lines = [head]
    if s.get("error"):
        lines.append(f"- **Error:** `{s['error']}`")
        lines.append("")
        return lines

    if scoring == "mcq":
        chosen = detail.get("chosen")
        expected = detail.get("expected")
        lines.append(f"- **Chosen:** `{chosen}`  vs  **Expected:** `{expected}`")
        lines.append(f"- **Response:** {_preview(s.get('response_text'), 200)}")
    elif scoring == "keyword":
        keyword = detail.get("keyword", s.get("correct_answer", ""))
        lines.append(f"- **Missing keyword:** `{keyword}`")
        lines.append(f"- **Response:** {_preview(s.get('response_text'), 200)}")
    elif scoring in ("open-ended", "rubric") or detail.get("automated"):
        auto = detail.get("automated", {}) or {}
        judge = detail.get("judge", {}) or {}
        missing = auto.get("must_mention_missing") or []
        red = auto.get("red_flag_hits") or []
        verdict = judge.get("verdict") or "?"
        evidence = judge.get("evidence") or ""
        if missing:
            lines.append(f"- **Missing must_mention:** `{', '.join(missing)}`")
        if red:
            lines.append(f"- **Red flags triggered:** `{', '.join(red)}`")
        lines.append(f"- **Judge verdict:** `{verdict}`")
        if evidence:
            lines.append(f"- **Judge evidence:** {_preview(evidence, 300)}")
        lines.append(f"- **Response:** {_preview(s.get('response_text'), 200)}")
    else:
        lines.append(f"- **Response:** {_preview(s.get('response_text'), 200)}")
    lines.append("")
    return lines


def _format_pass(s: dict) -> str:
    sid = s.get("id", "?")
    name = s.get("name", "?")
    cat = s.get("category", "?")
    return f"- {PASS_MARK} #{sid} `{name}` *({cat})*"


def _format_results_sections(scenarios: list[dict]) -> list[str]:
    passed = [s for s in scenarios if s.get("correct")]
    failed = [s for s in scenarios if not s.get("correct")]

    lines: list[str] = []
    lines.append(f"## Failures ({len(failed)})")
    lines.append("")
    if not failed:
        lines.append("_No failures — perfect run._")
        lines.append("")
    else:
        for s in failed:
            lines.extend(_format_failure(s))

    lines.append(f"## Passes ({len(passed)})")
    lines.append("")
    if not passed:
        lines.append("_No passes._")
        lines.append("")
    else:
        for s in passed:
            lines.append(_format_pass(s))
        lines.append("")

    return lines


def build_report(data: dict, source_path: Path) -> str:
    """Assemble the full markdown report from a results dict."""
    scenarios = data.get("scenarios", [])
    model = data.get("model", "?")
    mode = data.get("mode", "?")
    lines: list[str] = []
    lines.append(f"# PM-Bench report — `{model}` ({mode})")
    lines.append("")
    lines.append(f"_Source: `{source_path.name}`_")
    lines.append("")
    lines.extend(_format_metadata(data))
    lines.extend(_format_overall(scenarios))
    lines.extend(_format_categories(scenarios))
    lines.extend(_format_results_sections(scenarios))
    return "\n".join(lines).rstrip() + "\n"


def _report_output_path(source: Path) -> Path:
    """Return the markdown report path derived from the source JSON."""
    stem = source.stem  # e.g. 20260414-120000_mcq_anthropic_claude-sonnet-4
    return source.parent / f"{stem}_report.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a markdown report from a PM-Bench results JSON.",
    )
    parser.add_argument("results_file", type=Path,
                        help="Path to a results/*.json file produced by run.py")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Override the output markdown path")
    parser.add_argument("--stdout-only", action="store_true",
                        help="Print the report but do not write to disk")
    args = parser.parse_args(argv)

    data = _load_results(args.results_file)
    report = build_report(data, args.results_file)
    # Best-effort UTF-8 stdout: on Windows the default cp1252 stdout will
    # raise on our tick marks. Reconfigure when possible and fall back to
    # writing bytes directly.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        print(report)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(report.encode("utf-8", errors="replace"))
        sys.stdout.buffer.write(b"\n")

    if not args.stdout_only:
        out = args.output or _report_output_path(args.results_file)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"\n[report written to: {out}]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
