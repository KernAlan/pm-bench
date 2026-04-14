"""Shared pytest fixtures for the PM-Bench test suite."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make the repo root importable so tests can `from run import ...`.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SCENARIOS_FILE = REPO_ROOT / "scenarios" / "scenarios.json"
OPEN_ENDED_FILE = REPO_ROOT / "scenarios" / "open-ended.json"
FIXTURES_DIR = REPO_ROOT / "fixtures"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def scenarios_raw() -> dict:
    return json.loads(SCENARIOS_FILE.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def open_ended_raw() -> dict:
    return json.loads(OPEN_ENDED_FILE.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def scenarios(scenarios_raw) -> list[dict]:
    if isinstance(scenarios_raw, dict) and "scenarios" in scenarios_raw:
        return scenarios_raw["scenarios"]
    return scenarios_raw


@pytest.fixture(scope="session")
def open_ended(open_ended_raw) -> list[dict]:
    if isinstance(open_ended_raw, dict) and "scenarios" in open_ended_raw:
        return open_ended_raw["scenarios"]
    return open_ended_raw


# --- sample scoring scenarios reused across test_scoring.py ---------------

@pytest.fixture
def mcq_scenario() -> dict:
    return {
        "id": 101,
        "name": "example_mcq",
        "category": "Memory Recall",
        "scoring": "mcq",
        "correct_answer": "B",
        "trigger": "Which one?\nA) x\nB) y\nC) z\nD) w",
        "workspace_files": {},
    }


@pytest.fixture
def keyword_scenario() -> dict:
    return {
        "id": 102,
        "name": "example_keyword",
        "category": "Proactive Outreach",
        "scoring": "keyword",
        "correct_answer": "Sarah",
        "trigger": "Who owns this?",
        "workspace_files": {},
    }


@pytest.fixture
def rubric_scenario() -> dict:
    return {
        "id": 103,
        "name": "example_open_ended",
        "category": "Superhuman PM Judgment",
        "trigger": "Summarize the day.",
        "rubric": {
            "must_mention": ["events", "collision"],
            "should_mention": ["coordinate", "schema"],
            "red_flags": ["everything looks good", "no conflicts"],
        },
        "judge_prompt": "Pass if the response flags the collision.",
    }
