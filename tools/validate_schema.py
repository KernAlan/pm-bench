#!/usr/bin/env python3
"""Standalone schema validator for PM-Bench.

Runs without pytest so it can be used directly in CI or pre-commit hooks.
Exits 0 on success and 1 on any validation error. Prints a summary of
every error found (does not short-circuit on the first failure).

Usage:
    python tools/validate_schema.py
    python tools/validate_schema.py --repo-root /path/to/pm-bench
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MCQ_REQUIRED_FIELDS = {
    "id", "name", "category", "workspace_files", "trigger",
    "correct_answer", "expected_tools", "scoring",
}

OPEN_ENDED_REQUIRED_FIELDS = {
    "id", "source_mcq_id", "name", "category", "workspace_files",
    "trigger", "rubric", "judge_prompt",
}

VALID_SCORING = {"mcq", "keyword", "tool_use"}
MCQ_LETTERS = {"A", "B", "C", "D"}


class Validator:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.fixtures_dir = repo_root / "fixtures"
        self.scenarios_path = repo_root / "scenarios" / "scenarios.json"
        self.open_ended_path = repo_root / "scenarios" / "open-ended.json"
        self.errors: list[str] = []

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def _load(self, path: Path) -> list[dict] | None:
        if not path.exists():
            self.err(f"File not found: {path}")
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            self.err(f"{path.name}: invalid JSON — {e}")
            return None
        if isinstance(data, dict) and "scenarios" in data:
            return data["scenarios"]
        if isinstance(data, list):
            return data
        self.err(f"{path.name}: unexpected top-level structure")
        return None

    def _check_fixture_ref(self, tag: str, sid, ref: str) -> None:
        if not ref.startswith("@fixtures/"):
            return
        if "\\" in ref:
            self.err(f"{tag} #{sid}: fixture ref uses backslash: {ref!r}")
        path = self.fixtures_dir / ref[len("@fixtures/"):]
        if not path.exists():
            self.err(f"{tag} #{sid}: missing fixture {path}")

    # ------------------------------------------------------------------
    # scenarios.json
    # ------------------------------------------------------------------
    def validate_mcq(self, scenarios: list[dict]) -> None:
        if not scenarios:
            self.err("scenarios.json: no scenarios found")
            return

        ids = []
        for s in scenarios:
            sid = s.get("id", "?")
            missing = MCQ_REQUIRED_FIELDS - set(s.keys())
            if missing:
                self.err(f"MCQ #{sid}: missing fields {sorted(missing)}")
                continue

            if not isinstance(sid, int):
                self.err(f"MCQ id {sid!r} is not an int")
            else:
                ids.append(sid)

            if s["scoring"] not in VALID_SCORING:
                self.err(f"MCQ #{sid}: invalid scoring {s['scoring']!r}")

            if not (isinstance(s["trigger"], str) and s["trigger"].strip()):
                self.err(f"MCQ #{sid}: empty trigger")

            if not (isinstance(s["name"], str) and s["name"].strip()):
                self.err(f"MCQ #{sid}: empty name")

            if not (isinstance(s["category"], str) and s["category"].strip()):
                self.err(f"MCQ #{sid}: empty category")

            if not isinstance(s["expected_tools"], list):
                self.err(f"MCQ #{sid}: expected_tools not a list")

            wf = s["workspace_files"]
            if not isinstance(wf, dict):
                self.err(f"MCQ #{sid}: workspace_files not a dict")
            else:
                for fn, ref in wf.items():
                    if not (isinstance(fn, str) and fn.strip()):
                        self.err(f"MCQ #{sid}: empty workspace_files key")
                    if not (isinstance(ref, str) and ref):
                        self.err(f"MCQ #{sid}: empty ref for {fn!r}")
                    elif isinstance(ref, str):
                        self._check_fixture_ref("MCQ", sid, ref)

            scoring = s.get("scoring")
            ans = s.get("correct_answer", "")
            if scoring == "mcq":
                if not (isinstance(ans, str)
                        and ans.strip().upper() in MCQ_LETTERS):
                    self.err(
                        f"MCQ #{sid} (mcq): correct_answer {ans!r} not A/B/C/D"
                    )
            elif scoring == "keyword":
                if not (isinstance(ans, str) and ans.strip()):
                    self.err(f"MCQ #{sid} (keyword): empty correct_answer")
            elif scoring == "tool_use":
                tools = s.get("expected_tools")
                # Empty list is allowed: "negative" tool_use cases assert
                # the agent should take no tool action. Only reject if
                # the field is missing or not a list.
                if not isinstance(tools, list):
                    self.err(
                        f"MCQ #{sid} (tool_use): expected_tools not a list"
                    )
                else:
                    for t in tools:
                        if not (isinstance(t, str) and t.strip()):
                            self.err(
                                f"MCQ #{sid} (tool_use): non-string tool {t!r}"
                            )

        if len(ids) != len(set(ids)):
            dupes = sorted({x for x in ids if ids.count(x) > 1})
            self.err(f"scenarios.json: duplicate ids {dupes}")

    # ------------------------------------------------------------------
    # open-ended.json
    # ------------------------------------------------------------------
    def validate_open_ended(
        self, open_ended: list[dict], mcq_ids: set[int]
    ) -> None:
        if not open_ended:
            self.err("open-ended.json: no scenarios found")
            return

        ids = []
        for s in open_ended:
            sid = s.get("id", "?")
            missing = OPEN_ENDED_REQUIRED_FIELDS - set(s.keys())
            if missing:
                self.err(
                    f"Open-ended #{sid}: missing fields {sorted(missing)}"
                )
                continue

            if not isinstance(sid, int):
                self.err(f"Open-ended id {sid!r} is not an int")
            else:
                ids.append(sid)

            if not (isinstance(s["trigger"], str) and s["trigger"].strip()):
                self.err(f"Open-ended #{sid}: empty trigger")

            if not (isinstance(s["judge_prompt"], str)
                    and s["judge_prompt"].strip()):
                self.err(f"Open-ended #{sid}: empty judge_prompt")

            if not (isinstance(s["name"], str) and s["name"].strip()):
                self.err(f"Open-ended #{sid}: empty name")
            if not (isinstance(s["category"], str) and s["category"].strip()):
                self.err(f"Open-ended #{sid}: empty category")

            rubric = s["rubric"]
            if not isinstance(rubric, dict):
                self.err(f"Open-ended #{sid}: rubric not a dict")
            else:
                for key in ("must_mention", "should_mention", "red_flags"):
                    if key not in rubric:
                        self.err(f"Open-ended #{sid}: rubric missing {key}")
                    elif not isinstance(rubric[key], list):
                        self.err(
                            f"Open-ended #{sid}: rubric.{key} not a list"
                        )

            src = s.get("source_mcq_id")
            if not isinstance(src, int):
                self.err(
                    f"Open-ended #{sid}: source_mcq_id {src!r} not an int"
                )
            elif src not in mcq_ids:
                self.err(
                    f"Open-ended #{sid}: source_mcq_id={src} not in "
                    "scenarios.json"
                )

            wf = s.get("workspace_files", {})
            if not isinstance(wf, dict):
                self.err(f"Open-ended #{sid}: workspace_files not a dict")
            else:
                for fn, ref in wf.items():
                    if not (isinstance(fn, str) and fn.strip()):
                        self.err(f"Open-ended #{sid}: empty workspace key")
                    if not (isinstance(ref, str) and ref):
                        self.err(
                            f"Open-ended #{sid}: empty ref for {fn!r}"
                        )
                    elif isinstance(ref, str):
                        self._check_fixture_ref("Open-ended", sid, ref)

        if len(ids) != len(set(ids)):
            dupes = sorted({x for x in ids if ids.count(x) > 1})
            self.err(f"open-ended.json: duplicate ids {dupes}")

    # ------------------------------------------------------------------
    # orphans
    # ------------------------------------------------------------------
    def validate_fixtures(
        self, scenarios: list[dict], open_ended: list[dict]
    ) -> None:
        if not self.fixtures_dir.exists():
            self.err(f"Fixtures directory not found: {self.fixtures_dir}")
            return

        def collect(dataset: list[dict]) -> set[str]:
            refs: set[str] = set()
            for s in dataset:
                for ref in s.get("workspace_files", {}).values():
                    if isinstance(ref, str) and ref.startswith("@fixtures/"):
                        refs.add(ref[len("@fixtures/"):])
            return refs

        referenced = collect(scenarios) | collect(open_ended)
        on_disk: set[str] = set()
        for p in self.fixtures_dir.rglob("*"):
            if p.is_file():
                rel = p.relative_to(self.fixtures_dir).as_posix()
                # The variants/ subtree is produced by
                # tools/workspace_variants.py and is referenced only by
                # the variant scenarios files, not by the canonical one.
                if rel.startswith("variants/"):
                    continue
                on_disk.add(rel)

        for orphan in sorted(on_disk - referenced):
            self.err(f"Orphan fixture (not referenced): {orphan}")

    # ------------------------------------------------------------------
    def run(self) -> int:
        scenarios = self._load(self.scenarios_path) or []
        open_ended = self._load(self.open_ended_path) or []

        self.validate_mcq(scenarios)
        mcq_ids = {s["id"] for s in scenarios if isinstance(s.get("id"), int)}
        self.validate_open_ended(open_ended, mcq_ids)
        self.validate_fixtures(scenarios, open_ended)

        if self.errors:
            print(f"PM-Bench schema validation: FAIL ({len(self.errors)} issue(s))")
            for e in self.errors:
                print(f"  - {e}")
            return 1

        print(
            f"PM-Bench schema validation: OK "
            f"({len(scenarios)} MCQ, {len(open_ended)} open-ended)"
        )
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Path to the pm-bench repo root (default: parent of this file)",
    )
    args = parser.parse_args()
    return Validator(args.repo_root).run()


if __name__ == "__main__":
    sys.exit(main())
