"""Schema validation for scenarios.json and open-ended.json."""
from __future__ import annotations

from pathlib import Path

import pytest

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


# ---------------------------------------------------------------------------
# scenarios.json
# ---------------------------------------------------------------------------


def test_scenarios_file_loads(scenarios):
    assert isinstance(scenarios, list)
    assert len(scenarios) > 0


@pytest.fixture(scope="module")
def _ids_mcq(scenarios):
    return [s.get("id") for s in scenarios]


def test_scenarios_ids_are_integers_and_unique(_ids_mcq):
    for sid in _ids_mcq:
        assert isinstance(sid, int), f"Scenario id {sid!r} is not an int"
    assert len(_ids_mcq) == len(set(_ids_mcq)), "Duplicate ids in scenarios.json"


def test_scenarios_have_required_fields(scenarios):
    for s in scenarios:
        missing = MCQ_REQUIRED_FIELDS - set(s.keys())
        assert not missing, f"Scenario #{s.get('id')} missing fields: {missing}"


def test_scenarios_scoring_is_valid(scenarios):
    for s in scenarios:
        assert s["scoring"] in VALID_SCORING, (
            f"Scenario #{s['id']} has invalid scoring {s['scoring']!r}"
        )


def test_scenarios_trigger_is_nonempty(scenarios):
    for s in scenarios:
        assert isinstance(s["trigger"], str) and s["trigger"].strip(), (
            f"Scenario #{s['id']} has empty trigger"
        )


def test_scenarios_name_is_nonempty_string(scenarios):
    for s in scenarios:
        assert isinstance(s["name"], str) and s["name"].strip()


def test_scenarios_category_is_nonempty_string(scenarios):
    for s in scenarios:
        assert isinstance(s["category"], str) and s["category"].strip()


def test_scenarios_expected_tools_is_list(scenarios):
    for s in scenarios:
        assert isinstance(s["expected_tools"], list), (
            f"Scenario #{s['id']} expected_tools is not a list"
        )


def test_scenarios_workspace_files_is_dict(scenarios):
    for s in scenarios:
        wf = s["workspace_files"]
        assert isinstance(wf, dict), (
            f"Scenario #{s['id']} workspace_files is not a dict"
        )


def test_scenarios_workspace_files_values(scenarios, fixtures_dir: Path):
    for s in scenarios:
        for filename, ref in s["workspace_files"].items():
            assert isinstance(filename, str) and filename.strip()
            assert isinstance(ref, str) and ref, (
                f"Scenario #{s['id']} has empty workspace_files entry {filename!r}"
            )
            if ref.startswith("@fixtures/"):
                path = fixtures_dir / ref[len("@fixtures/"):]
                assert path.exists(), (
                    f"Scenario #{s['id']} references missing fixture: {path}"
                )


def test_mcq_scoring_correct_answer_is_single_letter(scenarios):
    for s in scenarios:
        if s["scoring"] != "mcq":
            continue
        ans = s.get("correct_answer", "")
        assert isinstance(ans, str)
        stripped = ans.strip().upper()
        assert stripped in MCQ_LETTERS, (
            f"Scenario #{s['id']} (mcq) has invalid correct_answer "
            f"{ans!r}; expected one of A/B/C/D"
        )


def test_keyword_scoring_correct_answer_nonempty(scenarios):
    for s in scenarios:
        if s["scoring"] != "keyword":
            continue
        ans = s.get("correct_answer", "")
        assert isinstance(ans, str) and ans.strip(), (
            f"Scenario #{s['id']} (keyword) has empty correct_answer"
        )


def test_tool_use_scoring_expected_tools_well_formed(scenarios):
    """tool_use scenarios either specify the tools that should be called
    (non-empty list) or assert that no tool should be called (empty list
    — negative test, e.g. the agent recognizes casual banter and should
    not act). Both forms are valid; this test only enforces that the
    field is a list of non-empty strings."""
    for s in scenarios:
        if s["scoring"] != "tool_use":
            continue
        tools = s["expected_tools"]
        assert isinstance(tools, list), (
            f"Scenario #{s['id']} (tool_use) expected_tools not a list"
        )
        for t in tools:
            assert isinstance(t, str) and t.strip(), (
                f"Scenario #{s['id']} (tool_use) has non-string or empty "
                f"tool entry: {t!r}"
            )


# ---------------------------------------------------------------------------
# open-ended.json
# ---------------------------------------------------------------------------


def test_open_ended_file_loads(open_ended):
    assert isinstance(open_ended, list)
    assert len(open_ended) > 0


def test_open_ended_have_required_fields(open_ended):
    for s in open_ended:
        missing = OPEN_ENDED_REQUIRED_FIELDS - set(s.keys())
        assert not missing, (
            f"Open-ended scenario #{s.get('id')} missing fields: {missing}"
        )


def test_open_ended_ids_unique(open_ended):
    ids = [s["id"] for s in open_ended]
    assert len(ids) == len(set(ids)), "Duplicate ids in open-ended.json"
    for sid in ids:
        assert isinstance(sid, int)


def test_open_ended_trigger_nonempty(open_ended):
    for s in open_ended:
        assert isinstance(s["trigger"], str) and s["trigger"].strip()


def test_open_ended_judge_prompt_nonempty(open_ended):
    for s in open_ended:
        assert isinstance(s["judge_prompt"], str) and s["judge_prompt"].strip()


def test_open_ended_rubric_structure(open_ended):
    for s in open_ended:
        rubric = s["rubric"]
        assert isinstance(rubric, dict), (
            f"Open-ended #{s['id']} rubric is not a dict"
        )
        for key in ("must_mention", "should_mention", "red_flags"):
            assert key in rubric, (
                f"Open-ended #{s['id']} rubric missing {key!r}"
            )
            val = rubric[key]
            assert isinstance(val, list), (
                f"Open-ended #{s['id']} rubric.{key} is not a list"
            )
            for item in val:
                assert isinstance(item, str) and item.strip()


def test_open_ended_source_mcq_id_is_valid(open_ended, scenarios):
    mcq_ids = {s["id"] for s in scenarios}
    for s in open_ended:
        src = s["source_mcq_id"]
        assert isinstance(src, int), (
            f"Open-ended #{s['id']} source_mcq_id is not int"
        )
        assert src in mcq_ids, (
            f"Open-ended #{s['id']} source_mcq_id={src} is not present in "
            f"scenarios.json"
        )


def test_open_ended_workspace_files(open_ended, fixtures_dir: Path):
    for s in open_ended:
        wf = s["workspace_files"]
        assert isinstance(wf, dict)
        for filename, ref in wf.items():
            assert isinstance(filename, str) and filename.strip()
            assert isinstance(ref, str) and ref
            if ref.startswith("@fixtures/"):
                path = fixtures_dir / ref[len("@fixtures/"):]
                assert path.exists(), (
                    f"Open-ended #{s['id']} references missing fixture: {path}"
                )


def test_open_ended_name_and_category_nonempty(open_ended):
    for s in open_ended:
        assert isinstance(s["name"], str) and s["name"].strip()
        assert isinstance(s["category"], str) and s["category"].strip()
