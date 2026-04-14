"""End-to-end tests for the mock LLM provider.

These exercise `python run.py --provider mock` as a subprocess so that we
cover the full pipeline — argument parsing, scenario loading, context
assembly, dispatch, scoring, and result persistence — without needing any
API credentials. That makes them safe to run in CI.

The mock provider is deterministic:
- `perfect` mode returns the correct MCQ letter and a text that satisfies
  every open-ended rubric's must_mention set.
- `weak` mode returns a deterministic wrong letter (or a red-flag phrase
  for open-ended scenarios).
- `random` mode returns a pseudo-random letter seeded by scenario id, which
  approximates a ~25% baseline over a large enough MCQ subset.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"


def _run(args: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    """Invoke run.py with the given args under the current interpreter.

    Captures stdout/stderr as text. Raises on nonzero exit code so tests
    surface pipeline breakage fast rather than miscounting accuracy.
    """
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, str(REPO_ROOT / "run.py"), *args]
    proc = subprocess.run(
        cmd, cwd=REPO_ROOT, env=env,
        capture_output=True, text=True, timeout=timeout,
        encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"run.py exited {proc.returncode}\n"
            f"argv: {args}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc


def _latest_result(glob: str) -> dict:
    """Return the most recent results JSON matching a glob pattern.

    We match by mode/provider/model in the filename so parallel test runs
    with different mock modes don't interfere with each other.
    """
    matches = sorted(RESULTS_DIR.glob(glob), key=lambda p: p.stat().st_mtime)
    assert matches, f"No results file matched: {glob}"
    return json.loads(matches[-1].read_text(encoding="utf-8"))


class TestMockPerfectMode:
    def test_superhuman_only_scores_100_percent(self):
        """Perfect mock should ace the Superhuman 20 MCQ subset."""
        _run(["--provider", "mock", "--mock-mode", "perfect",
              "--superhuman-only"])
        data = _latest_result("*_mcq_mock_mock-perfect.json")
        assert data["total"] == 20
        assert data["correct"] == 20, (
            f"Perfect mock should pass all 20 Superhuman MCQ, got "
            f"{data['correct']}/{data['total']}"
        )

    def test_open_ended_single_scenario_passes(self):
        """Mock judge returns PASS and mock subject hits every must_mention."""
        _run(["--provider", "mock", "--mode", "open-ended", "--scenario", "1"])
        data = _latest_result("*_open-ended_mock_mock-perfect.json")
        assert data["total"] == 1
        assert data["correct"] == 1
        sc = data["scenarios"][0]
        assert sc["score_detail"]["judge"]["verdict"] == "PASS"
        assert sc["score_detail"]["automated"]["automated_pass"] is True


class TestMockWeakMode:
    def test_weak_mode_scores_zero(self):
        """Weak mock deliberately returns wrong letters — should score 0%."""
        _run(["--provider", "mock", "--mock-mode", "weak",
              "--superhuman-only"])
        data = _latest_result("*_mcq_mock_mock-weak.json")
        assert data["total"] == 20
        assert data["correct"] == 0, (
            f"Weak mock should score 0/20, got {data['correct']}/20"
        )


class TestMockRandomMode:
    def test_random_mode_baseline(self):
        """Random mock should land near 25% on a 20-scenario MCQ subset.

        Random chance on 4-choice MCQ is 25%. With n=20 we expect most
        draws to fall within roughly 5%–50%. We allow 0%–55% to stay
        robust under deterministic seeding without being vacuous.
        """
        _run(["--provider", "mock", "--mock-mode", "random",
              "--superhuman-only"])
        data = _latest_result("*_mcq_mock_mock-random.json")
        assert data["total"] == 20
        pct = data["correct"] / data["total"] * 100
        assert 0 <= pct <= 55, (
            f"Random mock accuracy {pct:.1f}% is way outside the expected "
            f"~25% band for 4-choice MCQ"
        )

    def test_random_mode_is_deterministic(self):
        """Two random-mode runs over the same subset must produce the same
        score — random-mode uses scenario id as a seed for reproducibility.
        """
        _run(["--provider", "mock", "--mock-mode", "random",
              "--superhuman-only"])
        first = _latest_result("*_mcq_mock_mock-random.json")["correct"]
        _run(["--provider", "mock", "--mock-mode", "random",
              "--superhuman-only"])
        second = _latest_result("*_mcq_mock_mock-random.json")["correct"]
        assert first == second


class TestMockDispatchBackwardsCompat:
    """Ensure adding `scenario` to dispatch did not break real-provider calls.

    We can't actually hit anthropic/openai in CI, but we can verify the
    function signatures still accept the old positional call shape used by
    the rest of the codebase and by any external consumers.
    """

    def test_dispatch_ignores_scenario_for_real_providers(self, monkeypatch):
        from run import dispatch

        captured: dict = {}

        def fake_anthropic(messages, model, max_tokens=1024):
            captured["messages"] = messages
            captured["model"] = model
            captured["max_tokens"] = max_tokens
            return {"text": "stubbed", "tool_calls": []}

        monkeypatch.setattr("run.call_anthropic", fake_anthropic)
        result = dispatch("anthropic", [{"role": "user", "content": "hi"}],
                          "some-model", max_tokens=42,
                          scenario={"id": 1, "correct_answer": "B"},
                          mock_mode="perfect")
        assert result["text"] == "stubbed"
        assert captured["model"] == "some-model"
        assert captured["max_tokens"] == 42


@pytest.mark.parametrize("mode,expected_letter", [
    ("perfect", "B"),
    ("weak", None),  # anything except B
])
def test_call_mock_mcq_modes(mode, expected_letter):
    """Unit-level sanity check on call_mock for MCQ scenarios."""
    from run import call_mock, extract_mcq_choice

    scenario = {"id": 42, "correct_answer": "B", "scoring": "mcq"}
    resp = call_mock(messages=[{"role": "user", "content": "q"}],
                     model="mock", scenario=scenario, mode=mode)
    letter = extract_mcq_choice(resp["text"])
    if expected_letter is None:
        assert letter is not None
        assert letter != "B"
    else:
        assert letter == expected_letter


def test_call_mock_judge_always_passes():
    """Judge-shaped calls should always return VERDICT: PASS regardless of mode."""
    from run import call_mock

    judge_messages = [
        {"role": "system", "content": "You are an impartial grader evaluating a PM's response."},
        {"role": "user", "content": "grade this"},
    ]
    for mode in ("perfect", "weak", "random"):
        resp = call_mock(judge_messages, model="mock", mode=mode)
        assert "VERDICT: PASS" in resp["text"]
