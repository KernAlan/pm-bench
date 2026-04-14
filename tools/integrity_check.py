#!/usr/bin/env python3
"""
tools/integrity_check.py
========================

Regression test for PM-Bench's scoring pipeline. Runs the mock provider in
all three modes (perfect / random / weak) across all relevant subsets and
asserts the resulting scores land inside the expected bands.

Bands
-----
- ``perfect`` mode: must score **100%** across every subset.
- ``weak`` mode:    must score **0%** on every MCQ subset. Open-ended is
                    deliberately *not* checked for 0%: by design the mock
                    judge always returns ``VERDICT: PASS`` regardless of
                    mock_mode (see run.py call_mock docstring — the goal is
                    to test the pipeline's plumbing, not judge discernment).
                    So open-ended in weak mode will read 100%, which is
                    expected behavior, not a regression.
- ``random`` mode:  on the Superhuman 20 (4-way MCQ) must land within
                    **25% +/- 15%** -- i.e., roughly ``[10%, 40%]``. The band
                    is wide because n=20 is small and the deterministic
                    pseudo-random letter assignment is seeded from the
                    scenario id, not from run-time randomness.

Exit codes
----------
- ``0`` if every band is satisfied.
- ``1`` if any assertion fails (scoring infrastructure has regressed).

Usage
-----
    python tools/integrity_check.py

No arguments. No network. No API key. Intended for CI.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
RUN_PY = ROOT / "run.py"


def _run(args: list[str]) -> dict[str, Any]:
    """Invoke run.py with the given args, return the parsed summary JSON.

    We shell out rather than import run.main so we exercise the actual CLI
    contract (argparse wiring, result-file shape). The CLI writes a timestamped
    result file; we find it by taking the newest ``results/*.json``.
    """
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    before = {p.name for p in results_dir.glob("*.json")}

    cmd = [sys.executable, str(RUN_PY)] + args
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"\n[integrity_check] run.py failed:\n  cmd: {' '.join(cmd)}")
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        sys.exit(1)

    after = {p.name for p in results_dir.glob("*.json")}
    new_files = sorted(after - before)
    if not new_files:
        print(f"[integrity_check] expected new result file for: {' '.join(cmd)}",
              file=sys.stderr)
        sys.exit(1)
    newest = results_dir / new_files[-1]
    summary = json.loads(newest.read_text(encoding="utf-8"))
    # Clean up the file we generated to keep results/ tidy.
    try:
        newest.unlink()
    except OSError:
        pass
    return summary


def _pct(summary: dict[str, Any]) -> float:
    total = summary.get("total", 0) or 0
    correct = summary.get("correct", 0) or 0
    return (correct / total * 100.0) if total else 0.0


def _check_exact(label: str, pct: float, expected: float, failures: list[str]) -> None:
    if abs(pct - expected) > 1e-6:
        failures.append(f"{label}: expected {expected:.1f}% got {pct:.2f}%")
    print(f"  {label:<50} {pct:>6.2f}%  (expected {expected:.1f}%)")


def _check_band(label: str, pct: float, lo: float, hi: float,
                failures: list[str]) -> None:
    ok = lo <= pct <= hi
    status = "ok" if ok else "OUT OF BAND"
    if not ok:
        failures.append(f"{label}: expected {lo:.1f}%-{hi:.1f}% got {pct:.2f}%")
    print(f"  {label:<50} {pct:>6.2f}%  (band [{lo:.1f}%, {hi:.1f}%]) {status}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regression-check the mock provider's scoring across modes."
    )
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress per-check printouts; only print summary.")
    args = parser.parse_args()

    failures: list[str] = []

    # ---- Perfect mode: every subset should score 100% ----
    print("\n=== mock=perfect (expect 100%) ===")
    for label, extra in [
        ("mcq full (48 scorable)",       []),
        ("mcq superhuman 20",            ["--superhuman-only"]),
        ("open-ended 20",                ["--mode", "open-ended"]),
    ]:
        s = _run(["--provider", "mock", "--mock-mode", "perfect"] + extra)
        _check_exact(label, _pct(s), 100.0, failures)

    # ---- Weak mode: MCQ subsets should score 0%.
    # Open-ended is skipped because the mock judge always returns PASS by
    # design (see module docstring).
    print("\n=== mock=weak (expect 0% on MCQ subsets) ===")
    for label, extra in [
        ("mcq full (48 scorable)",       []),
        ("mcq superhuman 20",            ["--superhuman-only"]),
    ]:
        s = _run(["--provider", "mock", "--mock-mode", "weak"] + extra)
        _check_exact(label, _pct(s), 0.0, failures)

    # Sanity: the open-ended pipeline still runs end-to-end under weak mode.
    # We don't assert a specific score -- just that the run produced 20 items.
    s = _run(["--provider", "mock", "--mock-mode", "weak", "--mode", "open-ended"])
    if (s.get("total") or 0) != 20:
        failures.append(
            f"open-ended weak: expected total=20 got {s.get('total')}"
        )
    print(f"  {'open-ended 20 (pipeline smoke)':<50} "
          f"total={s.get('total')} correct={s.get('correct')}")

    # ---- Random mode: Superhuman 20 should hit 25% +/- 15% ----
    print("\n=== mock=random (expect ~25% +/- 15% on Superhuman 20) ===")
    s = _run(["--provider", "mock", "--mock-mode", "random", "--superhuman-only"])
    _check_band("mcq superhuman 20", _pct(s), 10.0, 40.0, failures)

    # Summary.
    print()
    if failures:
        print(f"INTEGRITY CHECK FAILED ({len(failures)} issue(s)):")
        for msg in failures:
            print(f"  - {msg}")
        return 1
    print("INTEGRITY CHECK PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
