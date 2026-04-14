#!/usr/bin/env python3
"""
huggingface/prepare_hf_dataset.py
=================================

Convert the repo-native PM-Bench scenario JSON into HuggingFace-ready JSONL
files. Each HF row is self-contained: fixture refs (``@fixtures/...``) are
resolved and inlined into a pre-rendered ``context`` string, so consumers of
the Hub dataset do not need the fixtures directory.

Output layout (written next to this script):

    huggingface/mcq.jsonl         -- 68 scenarios
    huggingface/open-ended.jsonl  -- 20 scenarios

Usage::

    python huggingface/prepare_hf_dataset.py

No arguments. Deterministic. Re-runs are idempotent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCENARIOS_FILE = ROOT / "scenarios" / "scenarios.json"
OPEN_ENDED_FILE = ROOT / "scenarios" / "open-ended.json"
FIXTURES_DIR = ROOT / "fixtures"

OUT_MCQ = HERE / "mcq.jsonl"
OUT_OPEN = HERE / "open-ended.jsonl"


def resolve_ref(ref: str) -> str:
    """Resolve ``@fixtures/...`` refs to file contents; pass literals through.

    Mirrors run.py's resolve_ref so the rendered context is byte-identical to
    what the runner feeds the model.
    """
    if ref.startswith("@fixtures/"):
        path = FIXTURES_DIR / ref[len("@fixtures/"):]
        if not path.exists():
            print(f"  [warn] fixture not found: {path}", file=sys.stderr)
            return ""
        return path.read_text(encoding="utf-8")
    return ref


def build_context(scenario: dict[str, Any]) -> str:
    """Flatten workspace_files into the ``--- filename ---`` block format."""
    parts: list[str] = []
    for filename, content_or_ref in scenario.get("workspace_files", {}).items():
        content = resolve_ref(content_or_ref)
        if content:
            parts.append(f"--- {filename} ---\n{content}")
    return "\n\n".join(parts)


def load_scenarios(path: Path) -> list[dict]:
    if not path.exists():
        print(f"Scenarios file not found: {path}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "scenarios" in data:
        return data["scenarios"]
    if isinstance(data, list):
        return data
    print("Unexpected scenarios file format.", file=sys.stderr)
    sys.exit(1)


def flatten_mcq(scenario: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": scenario["id"],
        "name": scenario.get("name", ""),
        "category": scenario.get("category", ""),
        "scoring": scenario.get("scoring", "mcq"),
        "context": build_context(scenario),
        "trigger": scenario.get("trigger", ""),
        "correct_answer": scenario.get("correct_answer", ""),
        "expected_tools": scenario.get("expected_tools", []) or [],
    }


def flatten_open(scenario: dict[str, Any]) -> dict[str, Any]:
    rubric = scenario.get("rubric", {}) or {}
    return {
        "id": scenario["id"],
        "source_mcq_id": scenario.get("source_mcq_id"),
        "name": scenario.get("name", ""),
        "category": scenario.get("category", ""),
        "context": build_context(scenario),
        "trigger": scenario.get("trigger", ""),
        "must_mention": rubric.get("must_mention", []) or [],
        "should_mention": rubric.get("should_mention", []) or [],
        "red_flags": rubric.get("red_flags", []) or [],
        "judge_prompt": scenario.get("judge_prompt", ""),
    }


def write_jsonl(rows: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    mcq_scenarios = load_scenarios(SCENARIOS_FILE)
    open_scenarios = load_scenarios(OPEN_ENDED_FILE)

    mcq_rows = [flatten_mcq(s) for s in mcq_scenarios]
    open_rows = [flatten_open(s) for s in open_scenarios]

    write_jsonl(mcq_rows, OUT_MCQ)
    write_jsonl(open_rows, OUT_OPEN)

    print(f"Wrote {len(mcq_rows)} rows to {OUT_MCQ.relative_to(ROOT)}")
    print(f"Wrote {len(open_rows)} rows to {OUT_OPEN.relative_to(ROOT)}")

    # Light sanity checks.
    cats: dict[str, int] = {}
    for r in mcq_rows:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    print("\nMCQ categories:")
    for k in sorted(cats):
        print(f"  {k:<40} {cats[k]:>3}")
    sh = sum(1 for r in mcq_rows if r["category"] == "Superhuman PM Judgment")
    print(f"\nSuperhuman subset size: {sh}")


if __name__ == "__main__":
    main()
