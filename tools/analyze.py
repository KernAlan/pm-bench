#!/usr/bin/env python3
"""
tools/analyze.py — Item Response Theory (IRT)-style analysis of PM-Bench results.

Reads every result file in `results/*.json` (as written by `run.py`) and
computes per-item psychometric statistics aggregated across all runs and all
models:

  - difficulty            1 - mean(correct)            higher = harder
  - discrimination        point-biserial correlation   higher = better at
                          between item correctness      separating strong
                          and overall model score       from weak models
  - guessing rate proxy   fraction of runs where the item was correct but
                          the overall model score was below 25% (random
                          baseline for 4-choice MCQ). MCQ items only.
  - floor effect          True if no run got it right  (0% correct)
  - ceiling effect        True if every run got it right (100% correct)

Outputs
-------
  analysis/item_stats.csv        one row per scenario
  analysis/analysis_report.md    human-readable summary

Usage
-----
    python tools/analyze.py

No arguments required. Auto-discovers `results/*.json`.

Dependencies
------------
  pandas (required)
  scipy  (optional; falls back to a numpy Pearson correlation if missing)
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ImportError:
    print("This tool requires pandas. Install with:  pip install pandas", file=sys.stderr)
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    print("This tool requires numpy. Install with:  pip install numpy", file=sys.stderr)
    sys.exit(1)

try:
    from scipy.stats import pointbiserialr  # type: ignore

    _HAVE_SCIPY = True
except ImportError:
    _HAVE_SCIPY = False


ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
ANALYSIS_DIR = ROOT / "analysis"


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_all_results() -> list[dict[str, Any]]:
    """Load every *.json file in results/. Each run is one dict."""
    if not RESULTS_DIR.exists():
        print(f"No results directory at {RESULTS_DIR}", file=sys.stderr)
        sys.exit(1)
    files = sorted(RESULTS_DIR.glob("*.json"))
    if not files:
        print(f"No result files found in {RESULTS_DIR}", file=sys.stderr)
        sys.exit(1)
    runs = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  [warn] skipping {f.name}: {e}", file=sys.stderr)
            continue
        data["_source_file"] = f.name
        runs.append(data)
    print(f"Loaded {len(runs)} result file(s) from {RESULTS_DIR}")
    return runs


def flatten(runs: list[dict[str, Any]]) -> pd.DataFrame:
    """One row per (run, scenario). Columns: run_id, model, mode, id, name,
    category, scoring, correct, total_score_pct."""
    rows: list[dict[str, Any]] = []
    for run in runs:
        model = run.get("model", "?")
        provider = run.get("provider", "?")
        mode = run.get("mode", "?")
        ts = run.get("timestamp", "?")
        run_id = f"{ts}|{provider}|{model}|{mode}"
        total = run.get("total") or len(run.get("scenarios", []))
        correct_n = run.get("correct", 0)
        pct = (correct_n / total) if total else 0.0
        for s in run.get("scenarios", []):
            rows.append({
                "run_id": run_id,
                "model": model,
                "provider": provider,
                "mode": mode,
                "id": s.get("id"),
                "name": s.get("name", ""),
                "category": s.get("category", ""),
                "scoring": s.get("scoring", ""),
                "correct": bool(s.get("correct", False)),
                "run_total_pct": pct,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def pearson_fallback(x: "np.ndarray", y: "np.ndarray") -> float:
    """Plain Pearson correlation using numpy. Returns NaN if undefined."""
    if len(x) < 2:
        return float("nan")
    sx, sy = x.std(), y.std()
    if sx == 0 or sy == 0:
        return float("nan")
    return float(((x - x.mean()) * (y - y.mean())).mean() / (sx * sy))


def point_biserial(item_correct: list[bool], totals: list[float]) -> float:
    """Point-biserial correlation. Equivalent to Pearson of bool-as-0/1
    against a continuous variable."""
    if len(item_correct) < 2:
        return float("nan")
    x = np.array([1 if c else 0 for c in item_correct], dtype=float)
    y = np.array(totals, dtype=float)
    if x.std() == 0 or y.std() == 0:
        return float("nan")
    if _HAVE_SCIPY:
        try:
            r, _ = pointbiserialr(x, y)
            return float(r)
        except Exception:
            pass
    return pearson_fallback(x, y)


def compute_item_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Per-scenario stats aggregated across all runs/models."""
    records: list[dict[str, Any]] = []
    for sid, grp in df.groupby("id"):
        n = len(grp)
        if n == 0:
            continue
        correct = grp["correct"].tolist()
        totals = grp["run_total_pct"].tolist()
        pct_correct = sum(1 for c in correct if c) / n
        difficulty = 1.0 - pct_correct
        disc = point_biserial(correct, totals)
        floor = pct_correct == 0.0
        ceiling = pct_correct == 1.0
        # Guessing proxy: MCQ-only, correct on the item but model below random.
        scoring = grp["scoring"].iloc[0] if len(grp) else ""
        guessing = float("nan")
        if scoring == "mcq":
            lucky = sum(
                1 for c, t in zip(correct, totals) if c and t < 0.25
            )
            guessing = lucky / n if n else float("nan")
        records.append({
            "id": sid,
            "name": grp["name"].iloc[0],
            "category": grp["category"].iloc[0],
            "scoring": scoring,
            "n_runs": n,
            "pct_correct": round(pct_correct, 4),
            "difficulty": round(difficulty, 4),
            "discrimination": None if math.isnan(disc) else round(disc, 4),
            "guessing_proxy": None if math.isnan(guessing) else round(guessing, 4),
            "floor": floor,
            "ceiling": ceiling,
        })
    out = pd.DataFrame(records).sort_values("id").reset_index(drop=True)
    return out


def difficulty_histogram(stats: pd.DataFrame) -> list[tuple[str, int]]:
    """Bin difficulty into [0,0.2), [0.2,0.4), ... [0.8,1.0]."""
    bins = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0001)]
    labels = ["0.0-0.2 (very easy)", "0.2-0.4 (easy)", "0.4-0.6 (medium)",
              "0.6-0.8 (hard)", "0.8-1.0 (very hard)"]
    out: list[tuple[str, int]] = []
    for (lo, hi), lab in zip(bins, labels):
        n = int(((stats["difficulty"] >= lo) & (stats["difficulty"] < hi)).sum())
        out.append((lab, n))
    return out


def category_means(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("category")["correct"].agg(["mean", "count"]).reset_index()
    g = g.rename(columns={"mean": "pct_correct", "count": "n_observations"})
    g["pct_correct"] = g["pct_correct"].round(4)
    return g.sort_values("pct_correct")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(stats: pd.DataFrame, df: pd.DataFrame, out_path: Path) -> None:
    lines: list[str] = []
    lines.append("# PM-Bench Item Analysis Report")
    lines.append("")
    lines.append(f"- Runs analyzed: **{df['run_id'].nunique()}**")
    lines.append(f"- Unique models: **{df['model'].nunique()}**")
    lines.append(f"- Scenarios with data: **{len(stats)}**")
    lines.append(f"- Total observations: **{len(df)}**")
    lines.append("")

    lines.append("## Difficulty Distribution")
    lines.append("")
    lines.append("| Bin | Count |")
    lines.append("|---|---|")
    for label, n in difficulty_histogram(stats):
        lines.append(f"| {label} | {n} |")
    lines.append("")

    floor = stats[stats["floor"]]
    ceiling = stats[stats["ceiling"]]
    lines.append(f"## Floor items (0% correct across all runs) — {len(floor)}")
    lines.append("")
    if len(floor):
        lines.append("Candidates to cut or revise (may be unanswerable, broken, "
                     "or mis-keyed).")
        lines.append("")
        lines.append("| id | name | category | scoring | n_runs |")
        lines.append("|---|---|---|---|---|")
        for _, r in floor.iterrows():
            lines.append(f"| {r['id']} | {r['name']} | {r['category']} | "
                         f"{r['scoring']} | {r['n_runs']} |")
    else:
        lines.append("_None._")
    lines.append("")

    lines.append(f"## Ceiling items (100% correct across all runs) — {len(ceiling)}")
    lines.append("")
    if len(ceiling):
        lines.append("Candidates to cut (too easy — no signal).")
        lines.append("")
        lines.append("| id | name | category | scoring | n_runs |")
        lines.append("|---|---|---|---|---|")
        for _, r in ceiling.iterrows():
            lines.append(f"| {r['id']} | {r['name']} | {r['category']} | "
                         f"{r['scoring']} | {r['n_runs']} |")
    else:
        lines.append("_None._")
    lines.append("")

    # Discrimination rankings (drop NaN).
    disc = stats.dropna(subset=["discrimination"]).copy()
    top = disc.sort_values("discrimination", ascending=False).head(10)
    bot = disc.sort_values("discrimination", ascending=True).head(10)

    lines.append("## Top 10 most discriminative items")
    lines.append("")
    lines.append("These items most strongly separate strong from weak models.")
    lines.append("")
    lines.append("| id | name | category | discrimination | difficulty |")
    lines.append("|---|---|---|---|---|")
    for _, r in top.iterrows():
        lines.append(f"| {r['id']} | {r['name']} | {r['category']} | "
                     f"{r['discrimination']:.3f} | {r['difficulty']:.3f} |")
    lines.append("")

    lines.append("## Bottom 10 least discriminative items")
    lines.append("")
    lines.append("Candidates to revise — these items don't help rank models.")
    lines.append("A negative value means the item is anti-correlated with ability "
                 "(strong models miss it, weak models get it right) and is a "
                 "priority to review.")
    lines.append("")
    lines.append("| id | name | category | discrimination | difficulty |")
    lines.append("|---|---|---|---|---|")
    for _, r in bot.iterrows():
        lines.append(f"| {r['id']} | {r['name']} | {r['category']} | "
                     f"{r['discrimination']:.3f} | {r['difficulty']:.3f} |")
    lines.append("")

    lines.append("## Per-category means (all runs pooled)")
    lines.append("")
    cm = category_means(df)
    lines.append("| category | pct_correct | n_observations |")
    lines.append("|---|---|---|")
    for _, r in cm.iterrows():
        lines.append(f"| {r['category']} | {r['pct_correct']:.3f} | "
                     f"{int(r['n_observations'])} |")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    runs = load_all_results()
    df = flatten(runs)
    if df.empty:
        print("No scenario rows found across result files.", file=sys.stderr)
        sys.exit(1)
    print(f"Flattened {len(df)} (run, scenario) observations across "
          f"{df['id'].nunique()} scenarios and {df['model'].nunique()} model(s).")
    if not _HAVE_SCIPY:
        print("  [note] scipy not installed; using numpy Pearson fallback for "
              "discrimination.")
    stats = compute_item_stats(df)

    ANALYSIS_DIR.mkdir(exist_ok=True)
    csv_path = ANALYSIS_DIR / "item_stats.csv"
    stats.to_csv(csv_path, index=False)
    print(f"Wrote {csv_path}")

    report_path = ANALYSIS_DIR / "analysis_report.md"
    write_report(stats, df, report_path)
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
