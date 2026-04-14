#!/usr/bin/env python3
"""
tools/compare_results.py
========================

Diff/comparison tool for PM-Bench result files.

Compares two result files produced by ``run.py`` and emits a markdown report
covering:

- Side-by-side overall scores (total, correct, percentage).
- Per-category comparison table.
- "Disagreement" sets:
    - Items A passed, B failed.
    - Items B passed, A failed.
- With ``--detailed``: full per-scenario diff of correctness.

Supports common comparison patterns:
- Same model on two benchmark versions / subsets.
- Two models on the same benchmark.
- Before/after tuning a prompt.

Usage
-----
    python tools/compare_results.py results/run_A.json results/run_B.json
    python tools/compare_results.py results/claude.json results/gpt4o.json --detailed
    python tools/compare_results.py A.json B.json --output diff.md
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def _label(summary: dict[str, Any], path: Path) -> str:
    """Short human label for a summary (provider/model, fallback to filename)."""
    provider = summary.get("provider") or "?"
    model = summary.get("model") or "?"
    if provider != "?" or model != "?":
        return f"{provider}/{model}"
    return path.stem


def _pct(correct: int, total: int) -> float:
    return (correct / total * 100.0) if total else 0.0


def _index_by_id(summary: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {r["id"]: r for r in summary.get("scenarios", []) if "id" in r}


def _category_breakdown(summary: dict[str, Any]) -> dict[str, tuple[int, int]]:
    """category -> (correct, total)."""
    cats: dict[str, list[bool]] = defaultdict(list)
    for r in summary.get("scenarios", []):
        cats[r.get("category", "?")].append(bool(r.get("correct", False)))
    return {cat: (sum(xs), len(xs)) for cat, xs in cats.items()}


def _section_overall(
    out: io.StringIO,
    a_path: Path, a_sum: dict[str, Any],
    b_path: Path, b_sum: dict[str, Any],
) -> None:
    a_label = _label(a_sum, a_path)
    b_label = _label(b_sum, b_path)
    a_tot = a_sum.get("total", 0)
    b_tot = b_sum.get("total", 0)
    a_cor = a_sum.get("correct", 0)
    b_cor = b_sum.get("correct", 0)

    out.write("## Overall\n\n")
    out.write("| Metric    | A                   | B                   | Delta (B - A) |\n")
    out.write("|-----------|---------------------|---------------------|---------------|\n")
    out.write(f"| File      | `{a_path.name}` | `{b_path.name}` | |\n")
    out.write(f"| Label     | {a_label} | {b_label} | |\n")
    out.write(f"| Mode      | {a_sum.get('mode','?')} | {b_sum.get('mode','?')} | |\n")
    out.write(f"| Total     | {a_tot} | {b_tot} | {b_tot - a_tot:+d} |\n")
    out.write(f"| Correct   | {a_cor} | {b_cor} | {b_cor - a_cor:+d} |\n")
    out.write(
        f"| Pct       | {_pct(a_cor, a_tot):.1f}% | {_pct(b_cor, b_tot):.1f}% | "
        f"{_pct(b_cor, b_tot) - _pct(a_cor, a_tot):+.1f} pp |\n\n"
    )


def _section_categories(
    out: io.StringIO,
    a_sum: dict[str, Any],
    b_sum: dict[str, Any],
) -> None:
    a_cats = _category_breakdown(a_sum)
    b_cats = _category_breakdown(b_sum)
    all_cats = sorted(set(a_cats) | set(b_cats))

    out.write("## Per-category\n\n")
    out.write("| Category | A score | A % | B score | B % | Delta (pp) |\n")
    out.write("|----------|---------|-----|---------|-----|------------|\n")
    for cat in all_cats:
        ac, at = a_cats.get(cat, (0, 0))
        bc, bt = b_cats.get(cat, (0, 0))
        a_pct = _pct(ac, at) if at else float("nan")
        b_pct = _pct(bc, bt) if bt else float("nan")
        if at and bt:
            delta = f"{b_pct - a_pct:+.1f}"
        else:
            delta = "-"
        a_s = f"{ac}/{at}" if at else "-"
        b_s = f"{bc}/{bt}" if bt else "-"
        a_p = f"{a_pct:.1f}%" if at else "-"
        b_p = f"{b_pct:.1f}%" if bt else "-"
        out.write(f"| {cat} | {a_s} | {a_p} | {b_s} | {b_p} | {delta} |\n")
    out.write("\n")


def _section_disagreements(
    out: io.StringIO,
    a_sum: dict[str, Any],
    b_sum: dict[str, Any],
) -> None:
    a_idx = _index_by_id(a_sum)
    b_idx = _index_by_id(b_sum)
    shared = sorted(set(a_idx) & set(b_idx))

    a_pass_b_fail = []
    b_pass_a_fail = []
    for sid in shared:
        a_ok = bool(a_idx[sid].get("correct", False))
        b_ok = bool(b_idx[sid].get("correct", False))
        if a_ok and not b_ok:
            a_pass_b_fail.append(sid)
        elif b_ok and not a_ok:
            b_pass_a_fail.append(sid)

    out.write("## Disagreements\n\n")
    out.write(f"- Shared scenarios: **{len(shared)}**\n")
    out.write(f"- A passed, B failed: **{len(a_pass_b_fail)}**\n")
    out.write(f"- B passed, A failed: **{len(b_pass_a_fail)}**\n")
    only_a = sorted(set(a_idx) - set(b_idx))
    only_b = sorted(set(b_idx) - set(a_idx))
    if only_a:
        out.write(f"- IDs only in A ({len(only_a)}): {only_a}\n")
    if only_b:
        out.write(f"- IDs only in B ({len(only_b)}): {only_b}\n")
    out.write("\n")

    def _table(ids: list[int], src_idx: dict[int, dict[str, Any]], heading: str) -> None:
        if not ids:
            return
        out.write(f"### {heading}\n\n")
        out.write("| ID | Name | Category |\n")
        out.write("|----|------|----------|\n")
        for sid in ids:
            row = src_idx[sid]
            out.write(
                f"| {sid} | {row.get('name','')} | {row.get('category','')} |\n"
            )
        out.write("\n")

    _table(a_pass_b_fail, a_idx, "A passed, B failed")
    _table(b_pass_a_fail, b_idx, "B passed, A failed")


def _section_detailed(
    out: io.StringIO,
    a_sum: dict[str, Any],
    b_sum: dict[str, Any],
) -> None:
    a_idx = _index_by_id(a_sum)
    b_idx = _index_by_id(b_sum)
    all_ids = sorted(set(a_idx) | set(b_idx))
    out.write("## Detailed per-scenario\n\n")
    out.write("| ID | Name | Category | A | B | Match |\n")
    out.write("|----|------|----------|---|---|-------|\n")
    for sid in all_ids:
        ar = a_idx.get(sid)
        br = b_idx.get(sid)
        name = (ar or br or {}).get("name", "")
        cat = (ar or br or {}).get("category", "")
        a_mark = "-" if ar is None else ("PASS" if ar.get("correct") else "FAIL")
        b_mark = "-" if br is None else ("PASS" if br.get("correct") else "FAIL")
        if ar is None or br is None:
            match = "-"
        elif bool(ar.get("correct")) == bool(br.get("correct")):
            match = "same"
        else:
            match = "diff"
        out.write(f"| {sid} | {name} | {cat} | {a_mark} | {b_mark} | {match} |\n")
    out.write("\n")


def build_report(
    a_path: Path, a_sum: dict[str, Any],
    b_path: Path, b_sum: dict[str, Any],
    detailed: bool,
) -> str:
    out = io.StringIO()
    out.write(f"# PM-Bench results diff\n\n")
    out.write(f"- **A**: `{a_path}` ({_label(a_sum, a_path)})\n")
    out.write(f"- **B**: `{b_path}` ({_label(b_sum, b_path)})\n\n")
    _section_overall(out, a_path, a_sum, b_path, b_sum)
    _section_categories(out, a_sum, b_sum)
    _section_disagreements(out, a_sum, b_sum)
    if detailed:
        _section_detailed(out, a_sum, b_sum)
    return out.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare two PM-Bench result files and produce a markdown diff.")
    parser.add_argument("a", help="Result file A (baseline)")
    parser.add_argument("b", help="Result file B (comparison)")
    parser.add_argument("--detailed", action="store_true",
                        help="Include full per-scenario table.")
    parser.add_argument("--output", type=str, default=None,
                        help="Write markdown to this file instead of stdout.")
    args = parser.parse_args()

    a_path = Path(args.a)
    b_path = Path(args.b)
    a_sum = load_summary(a_path)
    b_sum = load_summary(b_path)

    report = build_report(a_path, a_sum, b_path, b_sum, args.detailed)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        sys.stdout.write(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
