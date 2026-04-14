#!/usr/bin/env python3
"""
tools/multi_run.py — Multi-model baseline orchestrator for PM-Bench.

Wraps `run.py` to execute the benchmark against a list of models, in one
or both modes (mcq, open-ended), with multiple iterations per (model, mode)
pair to estimate variance.

For each run we invoke `run.py` as a subprocess so we inherit its full
scoring behavior. After all runs complete, we read the freshly-written
result files from `results/` and summarize.

Outputs
-------
  analysis/baselines.md
      - Per (model, mode) row: mean accuracy, std, 95% CI, per-category breakdown
      - 95% CI computed as  1.96 * std / sqrt(n)  (normal approximation)

Usage
-----
    python tools/multi_run.py \\
        --iterations 3 \\
        --models claude-sonnet-4-20250514 gpt-4o \\
        --modes mcq open-ended

    # Mixed providers via provider-map:
    python tools/multi_run.py --iterations 2 \\
        --models claude-sonnet-4-20250514 gpt-4o \\
        --provider-map 'claude-sonnet-4-20250514:anthropic,gpt-4o:openai'

    # Superhuman-only MCQ sample (faster):
    python tools/multi_run.py --iterations 3 --models gpt-4o \\
        --provider openai --modes mcq --superhuman-only

Dependencies
------------
  Just the Python stdlib. (pandas used if present for nicer CSV writing,
  but not required.)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
RUN_SCRIPT = ROOT / "run.py"
RESULTS_DIR = ROOT / "results"
ANALYSIS_DIR = ROOT / "analysis"


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


def check_keys(providers: set[str]) -> bool:
    ok = True
    if "anthropic" in providers and not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set — Anthropic models will fail.",
              file=sys.stderr)
        ok = False
    if "openai" in providers and not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set — OpenAI models will fail.",
              file=sys.stderr)
        ok = False
    return ok


# ---------------------------------------------------------------------------
# Run invocation
# ---------------------------------------------------------------------------

def snapshot_results() -> set[Path]:
    if not RESULTS_DIR.exists():
        return set()
    return set(RESULTS_DIR.glob("*.json"))


def invoke_run(provider: str, model: str, mode: str,
               superhuman_only: bool, judge_provider: str | None,
               judge_model: str | None) -> Path | None:
    """Run the benchmark once as a subprocess. Return the path to the newly
    created result file, or None on failure."""
    before = snapshot_results()
    cmd = [sys.executable, str(RUN_SCRIPT),
           "--provider", provider,
           "--model", model,
           "--mode", mode]
    if superhuman_only and mode == "mcq":
        cmd.append("--superhuman-only")
    if judge_provider:
        cmd.extend(["--judge-provider", judge_provider])
    if judge_model:
        cmd.extend(["--judge-model", judge_model])

    print(f"  invoking: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=str(ROOT), check=False)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        print(f"    subprocess failed: {e}", file=sys.stderr)
        return None
    if result.returncode != 0:
        print(f"    run.py exited with code {result.returncode}", file=sys.stderr)

    after = snapshot_results()
    new = sorted(after - before, key=lambda p: p.stat().st_mtime, reverse=True)
    if not new:
        return None
    return new[0]


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def load_accuracy(path: Path) -> tuple[float, dict[str, list[bool]]]:
    """Return (total_accuracy, per_category_lists_of_correctness)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    scenarios = data.get("scenarios", [])
    if not scenarios:
        return 0.0, {}
    correct = sum(1 for s in scenarios if s.get("correct"))
    acc = correct / len(scenarios)
    per_cat: dict[str, list[bool]] = defaultdict(list)
    for s in scenarios:
        per_cat[s.get("category", "?")].append(bool(s.get("correct")))
    return acc, dict(per_cat)


def std_sample(xs: list[float]) -> float:
    """Sample standard deviation; 0 for n<2."""
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def ci95(xs: list[float]) -> float:
    """95% CI half-width, normal approximation: 1.96 * std / sqrt(n)."""
    if len(xs) < 2:
        return 0.0
    return 1.96 * std_sample(xs) / math.sqrt(len(xs))


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_baselines(path: Path, per_combo: dict[tuple, dict[str, Any]]) -> None:
    lines: list[str] = []
    lines.append("# PM-Bench Baselines — Multi-run Summary")
    lines.append("")
    lines.append(f"_Generated: {datetime.now(timezone.utc).isoformat()}_")
    lines.append("")
    lines.append("| model | mode | iterations | mean | std | 95% CI (±) |")
    lines.append("|---|---|---|---|---|---|")
    for (model, mode), agg in sorted(per_combo.items()):
        accs = agg["accuracies"]
        if not accs:
            continue
        m = mean(accs)
        s = std_sample(accs)
        ci = ci95(accs)
        lines.append(f"| `{model}` | {mode} | {len(accs)} | {m:.3f} | "
                     f"{s:.3f} | {ci:.3f} |")
    lines.append("")

    lines.append("## Per-category breakdown")
    lines.append("")
    for (model, mode), agg in sorted(per_combo.items()):
        if not agg["accuracies"]:
            continue
        lines.append(f"### `{model}` — {mode}")
        lines.append("")
        lines.append("| category | mean | std | 95% CI (±) | n_iterations |")
        lines.append("|---|---|---|---|---|")
        cat_runs: dict[str, list[float]] = defaultdict(list)
        for per_cat in agg["per_cat_runs"]:
            for cat, flags in per_cat.items():
                if flags:
                    cat_runs[cat].append(sum(flags) / len(flags))
        for cat in sorted(cat_runs.keys()):
            xs = cat_runs[cat]
            lines.append(f"| {cat} | {mean(xs):.3f} | {std_sample(xs):.3f} | "
                         f"{ci95(xs):.3f} | {len(xs)} |")
        lines.append("")

    lines.append("## Source files")
    lines.append("")
    for (model, mode), agg in sorted(per_combo.items()):
        lines.append(f"- `{model}` / {mode}:")
        for p in agg["files"]:
            lines.append(f"    - `{p.name}`")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the benchmark multiple times across models and modes.")
    parser.add_argument("--iterations", type=int, default=3,
                        help="Iterations per (model, mode) for variance.")
    parser.add_argument("--models", nargs="+", required=True,
                        help="List of model names.")
    parser.add_argument("--modes", nargs="+",
                        choices=["mcq", "open-ended"],
                        default=["mcq"],
                        help="Modes to run (default: mcq).")
    parser.add_argument("--provider", choices=["anthropic", "openai"],
                        default="anthropic",
                        help="Default provider.")
    parser.add_argument("--provider-map", type=str, default=None,
                        help="Comma-separated model:provider pairs.")
    parser.add_argument("--superhuman-only", action="store_true",
                        help="MCQ only: run just Superhuman PM Judgment.")
    parser.add_argument("--judge-provider", default=None,
                        help="Judge provider for open-ended mode.")
    parser.add_argument("--judge-model", default=None,
                        help="Judge model for open-ended mode.")
    parser.add_argument("--sleep", type=float, default=1.0,
                        help="Seconds between runs.")
    args = parser.parse_args()

    providers = parse_provider_map(args.provider_map, args.models, args.provider)
    used_providers = set(providers.values())
    if args.judge_provider:
        used_providers.add(args.judge_provider)
    check_keys(used_providers)  # warn, don't abort — runs will surface errors

    if not RUN_SCRIPT.exists():
        print(f"run.py not found at {RUN_SCRIPT}", file=sys.stderr)
        sys.exit(1)

    per_combo: dict[tuple, dict[str, Any]] = {}
    for model in args.models:
        prov = providers[model]
        for mode in args.modes:
            key = (model, mode)
            per_combo[key] = {
                "accuracies": [], "per_cat_runs": [], "files": [],
            }
            print(f"\n=== {model} / {mode} ({args.iterations} iteration(s)) ===")
            for it in range(1, args.iterations + 1):
                print(f"  iteration {it}/{args.iterations}")
                out = invoke_run(prov, model, mode,
                                 args.superhuman_only,
                                 args.judge_provider, args.judge_model)
                if out is None:
                    print("    (no result file produced)")
                    continue
                acc, per_cat = load_accuracy(out)
                print(f"    accuracy: {acc:.3f}  ({out.name})")
                per_combo[key]["accuracies"].append(acc)
                per_combo[key]["per_cat_runs"].append(per_cat)
                per_combo[key]["files"].append(out)
                if it < args.iterations:
                    time.sleep(args.sleep)

    ANALYSIS_DIR.mkdir(exist_ok=True)
    out_path = ANALYSIS_DIR / "baselines.md"
    write_baselines(out_path, per_combo)
    print(f"\nWrote {out_path}")

    # Console summary.
    print("\nSummary:")
    for (model, mode), agg in sorted(per_combo.items()):
        accs = agg["accuracies"]
        if not accs:
            print(f"  {model} / {mode}: no successful runs")
            continue
        m = mean(accs)
        s = std_sample(accs)
        ci = ci95(accs)
        print(f"  {model} / {mode}:  mean={m:.3f}  std={s:.3f}  "
              f"ci95=±{ci:.3f}  (n={len(accs)})")


if __name__ == "__main__":
    main()
