"""Tests for the scoring functions in run.py.

Covers extract_mcq_choice, score_mcq, score_keyword, and
score_rubric_automated.

`extract_mcq_choice` is ordered by precedence (see run.py). Tests document
the actual implementation behavior — including cases where a simple regex
approach cannot disambiguate (e.g. "I considered A and B but C is right"
requires discourse-level understanding). Those cases are covered under the
`test_extract_mcq_choice_known_limitations` block so regressions are
detected if the implementation is later hardened.
"""
from __future__ import annotations

import pytest

from run import (
    extract_mcq_choice,
    score_keyword,
    score_mcq,
    score_rubric_automated,
)


# ---------------------------------------------------------------------------
# extract_mcq_choice  -- at least 40 cases
# ---------------------------------------------------------------------------


class TestExtractMcqChoiceBareLetter:
    def test_bare_A(self):
        assert extract_mcq_choice("A") == "A"

    def test_bare_B(self):
        assert extract_mcq_choice("B") == "B"

    def test_bare_C(self):
        assert extract_mcq_choice("C") == "C"

    def test_bare_D(self):
        assert extract_mcq_choice("D") == "D"

    def test_lowercase_b_is_normalized_to_upper(self):
        assert extract_mcq_choice("b") == "B"

    def test_lowercase_a(self):
        assert extract_mcq_choice("a") == "A"

    def test_bare_E_returns_none(self):
        assert extract_mcq_choice("E") is None

    def test_bare_Z_returns_none(self):
        assert extract_mcq_choice("Z") is None

    def test_bare_letter_with_surrounding_whitespace(self):
        assert extract_mcq_choice("   C   ") == "C"


class TestExtractMcqChoiceAnswerPatterns:
    def test_the_answer_is_letter(self):
        assert extract_mcq_choice("The answer is C") == "C"

    def test_the_correct_answer_is_letter(self):
        assert extract_mcq_choice("the correct answer is B") == "B"

    def test_correct_answer_colon(self):
        assert extract_mcq_choice("correct answer: D") == "D"

    def test_answer_colon(self):
        assert extract_mcq_choice("Answer: A") == "A"

    def test_answer_is_case_insensitive(self):
        assert extract_mcq_choice("ANSWER IS c") == "C"

    def test_answer_is_parenthesized(self):
        assert extract_mcq_choice("The answer is (B).") == "B"

    def test_x_is_correct(self):
        assert extract_mcq_choice("B is correct") == "B"

    def test_x_is_correct_mid_sentence(self):
        assert extract_mcq_choice("After reviewing, D is correct for this team.") == "D"


class TestExtractMcqChoicePickChoose:
    def test_i_would_pick(self):
        assert extract_mcq_choice("I would pick C") == "C"

    def test_go_with(self):
        assert extract_mcq_choice("Let's go with B") == "B"

    def test_choose(self):
        assert extract_mcq_choice("choose A") == "A"

    def test_select(self):
        assert extract_mcq_choice("select D") == "D"

    def test_option_letter(self):
        assert extract_mcq_choice("Option C") == "C"

    def test_option_letter_lowercase(self):
        assert extract_mcq_choice("option b") == "B"


class TestExtractMcqChoiceLeadingLetterDelimiter:
    def test_leading_letter_period(self):
        assert extract_mcq_choice("B.") == "B"

    def test_leading_letter_paren(self):
        assert extract_mcq_choice("B)") == "B"

    def test_leading_letter_colon(self):
        assert extract_mcq_choice("B:") == "B"

    def test_leading_letter_em_dash(self):
        # em-dash delimiter
        assert extract_mcq_choice("B \u2014 explanation") == "B"

    def test_leading_letter_comma(self):
        assert extract_mcq_choice("B, because we prefer scale.") == "B"

    def test_leading_letter_newline(self):
        assert extract_mcq_choice("B\nExplanation goes here.") == "B"

    def test_leading_letter_bolded(self):
        assert extract_mcq_choice("**B**") == "B"

    def test_leading_letter_parenthesized(self):
        assert extract_mcq_choice("(B)") == "B"

    def test_leading_letter_then_because(self):
        assert extract_mcq_choice("C because the billing migration is owned by Alan") == "C"


class TestExtractMcqChoiceOwnLine:
    def test_letter_on_own_line(self):
        # "B" by itself on a line, followed by a blank line and a paragraph.
        assert extract_mcq_choice("B\n\nExplanation about the rationale.") == "B"

    def test_bold_letter_on_own_line(self):
        assert extract_mcq_choice("**C**\n\nExplanation follows.") == "C"

    def test_parenthesized_letter_on_own_line(self):
        assert extract_mcq_choice("(D)\n\nSome justification.") == "D"


class TestExtractMcqChoiceFalsePositiveRejection:
    """These are the cases where a naive 'first letter' heuristic fails."""

    def test_not_b_c_is_correct(self):
        # The model negates B, then asserts C.
        assert extract_mcq_choice("Not B. C is correct.") == "C"

    def test_tempting_but_correct(self):
        assert extract_mcq_choice("B is tempting, but C is correct.") == "C"

    def test_wrong_wrong_correct(self):
        assert extract_mcq_choice("A is wrong. B is wrong. C is correct.") == "C"


class TestExtractMcqChoiceEdges:
    def test_empty_string(self):
        assert extract_mcq_choice("") is None

    def test_whitespace_only(self):
        assert extract_mcq_choice("   \n\t ") is None

    def test_answer_depends_on(self):
        # "The answer depends on..." should not latch onto any specific letter.
        assert extract_mcq_choice("The answer depends on context.") is None

    def test_multi_paragraph_with_letter_at_end(self):
        text = (
            "This is a nuanced question. There are several considerations "
            "to balance here, including team dynamics and runway.\n\n"
            "Answer: D"
        )
        # "Answer: D" anywhere in text triggers the explicit-answer branch.
        assert extract_mcq_choice(text) == "D"

    def test_letter_deep_in_explanation_no_pattern(self):
        # No selection cue at all -> returns None.
        text = (
            "I believe the team is still deciding between options here.\n"
            "More context would help."
        )
        assert extract_mcq_choice(text) is None


class TestExtractMcqChoiceDiscoursePatterns:
    """Discourse-level answer patterns (hardened in v1.0.1)."""

    def test_ultimately_c_is_the_answer(self):
        assert extract_mcq_choice(
            "This is a tough one. A looks plausible because... but "
            "ultimately, C is the answer."
        ) == "C"

    def test_considered_a_and_b_but_c_is_right(self):
        assert extract_mcq_choice("I considered A and B but C is right") == "C"

    def test_x_is_the_correct_answer(self):
        assert extract_mcq_choice("After analysis, B is the correct answer.") == "B"

    def test_therefore_b(self):
        assert extract_mcq_choice("Therefore, B.") == "B"

    def test_so_c_is_the_answer(self):
        assert extract_mcq_choice("So C is the answer.") == "C"

    def test_thus_b(self):
        assert extract_mcq_choice("Thus B") == "B"

    def test_my_answer_d(self):
        assert extract_mcq_choice("My answer: D") == "D"

    def test_final_answer_a(self):
        assert extract_mcq_choice("Final answer: A") == "A"

    def test_x_is_right_does_not_false_positive(self):
        # "Not B. C is right." should still reject B and return C.
        assert extract_mcq_choice("Not B. C is right.") == "C"


# ---------------------------------------------------------------------------
# score_mcq
# ---------------------------------------------------------------------------


class TestScoreMcq:
    def test_correct_bare_letter(self, mcq_scenario):
        r = score_mcq(mcq_scenario, {"text": "B"})
        assert r["correct"] is True
        assert r["chosen"] == "B"
        assert r["expected"] == "B"

    def test_correct_with_explanation(self, mcq_scenario):
        r = score_mcq(mcq_scenario, {"text": "B. Because the memory file says so."})
        assert r["correct"] is True

    def test_wrong_letter(self, mcq_scenario):
        r = score_mcq(mcq_scenario, {"text": "C is correct"})
        assert r["correct"] is False
        assert r["chosen"] == "C"

    def test_answer_pattern(self, mcq_scenario):
        r = score_mcq(mcq_scenario, {"text": "The answer is B"})
        assert r["correct"] is True

    def test_no_letter_found_returns_incorrect(self, mcq_scenario):
        r = score_mcq(mcq_scenario, {"text": "It depends."})
        assert r["correct"] is False
        assert r["chosen"] is None

    def test_rejects_misleading_preamble(self, mcq_scenario):
        r = score_mcq(mcq_scenario, {"text": "Not C. B is correct."})
        assert r["correct"] is True

    def test_empty_correct_answer_never_passes(self):
        scenario = {"id": 1, "correct_answer": ""}
        r = score_mcq(scenario, {"text": "A"})
        assert r["correct"] is False

    def test_multichar_correct_answer_never_passes(self):
        # defensive: if correct_answer has len > 1, should not pass.
        scenario = {"id": 1, "correct_answer": "BC"}
        r = score_mcq(scenario, {"text": "B"})
        assert r["correct"] is False

    def test_correct_answer_is_uppercased(self):
        scenario = {"id": 1, "correct_answer": "b"}
        r = score_mcq(scenario, {"text": "B"})
        assert r["correct"] is True
        assert r["expected"] == "B"

    def test_chosen_field_normalized_to_upper(self, mcq_scenario):
        r = score_mcq(mcq_scenario, {"text": "b"})
        assert r["chosen"] == "B"
        assert r["correct"] is True

    def test_all_four_letters(self):
        for letter in "ABCD":
            scenario = {"id": 1, "correct_answer": letter}
            r = score_mcq(scenario, {"text": f"{letter}. Done."})
            assert r["correct"] is True, f"Expected pass for {letter}"


# ---------------------------------------------------------------------------
# score_keyword
# ---------------------------------------------------------------------------


class TestScoreKeyword:
    def test_simple_match(self, keyword_scenario):
        r = score_keyword(keyword_scenario, {"text": "Sarah owns the frontend."})
        assert r["correct"] is True
        assert r["keyword"] == "Sarah"
        assert r["found"] is True

    def test_case_insensitive_match(self, keyword_scenario):
        r = score_keyword(keyword_scenario, {"text": "sarah is the owner"})
        assert r["correct"] is True

    def test_case_insensitive_match_all_caps(self, keyword_scenario):
        r = score_keyword(keyword_scenario, {"text": "SARAH knows this area."})
        assert r["correct"] is True

    def test_partial_word_match_behavior(self, keyword_scenario):
        # Documented behavior: plain substring match (no word-boundary
        # check). "sarah" appears inside "sarahstein@..." so this matches.
        r = score_keyword(keyword_scenario, {"text": "ping sarahstein@example.com"})
        assert r["correct"] is True
        assert r["found"] is True

    def test_missing_keyword(self, keyword_scenario):
        r = score_keyword(keyword_scenario, {"text": "No idea who owns it."})
        assert r["correct"] is False
        assert r["found"] is False

    def test_empty_keyword_never_matches(self):
        scenario = {"id": 1, "correct_answer": ""}
        r = score_keyword(scenario, {"text": "anything"})
        assert r["correct"] is False
        assert r["found"] is False

    def test_missing_correct_answer_never_matches(self):
        scenario = {"id": 1}
        r = score_keyword(scenario, {"text": "anything"})
        assert r["correct"] is False

    def test_multi_word_keyword(self):
        scenario = {"id": 1, "correct_answer": "Alan Kern"}
        r = score_keyword(scenario, {"text": "Ping Alan Kern about the schema."})
        assert r["correct"] is True

    def test_multi_word_keyword_missing(self):
        scenario = {"id": 1, "correct_answer": "Alan Kern"}
        r = score_keyword(scenario, {"text": "Ping Alan about the schema."})
        assert r["correct"] is False

    def test_keyword_with_surrounding_whitespace_stripped(self):
        scenario = {"id": 1, "correct_answer": "  Sarah  "}
        r = score_keyword(scenario, {"text": "Sarah is the owner."})
        assert r["correct"] is True

    def test_empty_response_text(self, keyword_scenario):
        r = score_keyword(keyword_scenario, {"text": ""})
        assert r["correct"] is False


# ---------------------------------------------------------------------------
# score_rubric_automated
# ---------------------------------------------------------------------------


class TestScoreRubricAutomated:
    def test_all_must_mention_no_red_flags(self, rubric_scenario):
        text = (
            "Both PRs modify the events table — there's a collision risk "
            "we need to coordinate on."
        )
        r = score_rubric_automated(rubric_scenario, {"text": text})
        assert r["automated_pass"] is True
        assert set(r["must_mention_hits"]) == {"events", "collision"}
        assert r["must_mention_missing"] == []
        assert r["red_flag_hits"] == []

    def test_missing_a_must_mention_fails(self, rubric_scenario):
        text = "Both PRs modify the events table. Needs coordination."
        r = score_rubric_automated(rubric_scenario, {"text": text})
        # "collision" is missing -> fail.
        assert r["automated_pass"] is False
        assert "collision" in r["must_mention_missing"]

    def test_red_flag_triggers_failure(self, rubric_scenario):
        text = (
            "The events collision is minor — honestly, everything looks "
            "good and we should ship."
        )
        r = score_rubric_automated(rubric_scenario, {"text": text})
        assert r["automated_pass"] is False
        assert "everything looks good" in r["red_flag_hits"]

    def test_should_mention_does_not_affect_pass(self, rubric_scenario):
        # Passes even without should_mention hits.
        text = "events collision detected."
        r = score_rubric_automated(rubric_scenario, {"text": text})
        assert r["automated_pass"] is True
        assert r["should_mention_hits"] == []

    def test_should_mention_hit_collected_but_not_required(self, rubric_scenario):
        text = "events collision — we need to coordinate."
        r = score_rubric_automated(rubric_scenario, {"text": text})
        assert r["automated_pass"] is True
        assert "coordinate" in r["should_mention_hits"]

    def test_case_insensitivity_for_must_mention(self, rubric_scenario):
        text = "EVENTS Collision detected across the two PRs."
        r = score_rubric_automated(rubric_scenario, {"text": text})
        assert r["automated_pass"] is True

    def test_case_insensitivity_for_red_flags(self, rubric_scenario):
        text = "events collision — NO CONFLICTS at all."
        r = score_rubric_automated(rubric_scenario, {"text": text})
        assert r["automated_pass"] is False
        assert "no conflicts" in r["red_flag_hits"]

    def test_empty_rubric_vacuously_passes(self):
        scenario = {"rubric": {}}
        r = score_rubric_automated(scenario, {"text": "anything"})
        # No must_mention, no red_flags -> vacuous pass.
        assert r["automated_pass"] is True
        assert r["must_mention_hits"] == []
        assert r["must_mention_missing"] == []
        assert r["red_flag_hits"] == []

    def test_missing_rubric_key(self):
        scenario = {}
        r = score_rubric_automated(scenario, {"text": "anything"})
        assert r["automated_pass"] is True

    def test_empty_response_with_must_mentions_fails(self, rubric_scenario):
        r = score_rubric_automated(rubric_scenario, {"text": ""})
        assert r["automated_pass"] is False
        assert set(r["must_mention_missing"]) == {"events", "collision"}

    def test_only_red_flags_listed_not_must(self):
        scenario = {"rubric": {"must_mention": [], "red_flags": ["bad phrase"]}}
        r = score_rubric_automated(scenario, {"text": "no bad phrase here? yes bad phrase."})
        assert r["automated_pass"] is False

    def test_only_must_listed_no_red(self):
        scenario = {"rubric": {"must_mention": ["alpha", "beta"]}}
        r = score_rubric_automated(scenario, {"text": "Alpha and beta are both here."})
        assert r["automated_pass"] is True
