#!/usr/bin/env python3
"""
PM-Bench Evaluation Runner

Runs scenarios against an LLM and scores responses. Supports two modes:

    MCQ mode (default): scenarios/scenarios.json, MCQ + keyword scoring
    Open-ended mode:    scenarios/open-ended.json, rubric + LLM-judge scoring

Usage:
    python run.py                                      # MCQ mode, all scorable
    python run.py --superhuman-only                    # MCQ, Superhuman 20
    python run.py --mode open-ended                    # Open-ended, 20 scenarios
    python run.py --mode open-ended --judge-model gpt-4o
    python run.py --provider openai --model gpt-4o
    python run.py --scenario 49                        # Single scenario by ID
    python run.py --dry-run                            # Print prompts only

Notes:
    - MCQ "tool_use" scenarios are always excluded (require external harness).
    - Open-ended mode requires BOTH a subject model (what's being tested) and
      a judge model (scores the response). Use different families to reduce
      self-bias when possible (e.g., subject=Claude, judge=GPT-4o).
"""

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SCENARIOS_FILE = ROOT / "scenarios" / "scenarios.json"
OPEN_ENDED_FILE = ROOT / "scenarios" / "open-ended.json"
FIXTURES_DIR = ROOT / "fixtures"
RESULTS_DIR = ROOT / "results"

# ---------------------------------------------------------------------------
# Context resolution
# ---------------------------------------------------------------------------

def resolve_ref(ref: str) -> str:
    """If ref starts with @fixtures/, load file content; otherwise return as-is."""
    if ref.startswith("@fixtures/"):
        path = FIXTURES_DIR / ref[len("@fixtures/"):]
        if not path.exists():
            print(f"  [warn] fixture not found: {path}", file=sys.stderr)
            return ""
        return path.read_text(encoding="utf-8")
    return ref


def build_context(scenario: dict) -> str:
    parts: list[str] = []
    for filename, content_or_ref in scenario.get("workspace_files", {}).items():
        content = resolve_ref(content_or_ref)
        if content:
            parts.append(f"--- {filename} ---\n{content}")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

MCQ_SYSTEM = (
    "You are the acting PM for this team. "
    "Use the workspace context provided to answer the question. "
    "For multiple-choice questions, respond with the correct letter "
    "(A, B, C, or D) and a brief explanation. "
    "Be concise and specific."
)

OPEN_ENDED_SYSTEM = (
    "You are the acting PM for this team. The workspace shows the team's "
    "current state, conversations, and context. Respond to the request in "
    "the user message with the judgment of a senior PM: catch what others "
    "might miss, flag genuine risks, and resist doing the literal ask if "
    "there is a more important concern. Be specific and grounded in the "
    "workspace evidence."
)


def build_messages(scenario: dict, context: str, system: str) -> list[dict]:
    user_content = ""
    if context:
        user_content += f"<workspace>\n{context}\n</workspace>\n\n"
    user_content += scenario["trigger"]
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]


# ---------------------------------------------------------------------------
# LLM clients
# ---------------------------------------------------------------------------

def call_anthropic(messages: list[dict], model: str, max_tokens: int = 1024) -> dict:
    try:
        from anthropic import Anthropic
    except ImportError:
        print("Install the anthropic SDK:  pip install anthropic", file=sys.stderr)
        sys.exit(1)
    client = Anthropic()
    system_text = ""
    chat_messages = []
    for m in messages:
        if m["role"] == "system":
            system_text += m["content"] + "\n"
        else:
            chat_messages.append(m)
    kwargs: dict[str, Any] = dict(model=model, max_tokens=max_tokens, messages=chat_messages)
    if system_text.strip():
        kwargs["system"] = system_text.strip()
    resp = client.messages.create(**kwargs)
    text_parts = []
    tool_calls = []
    for block in resp.content:
        if block.type == "text":
            text_parts.append(block.text)
        elif block.type == "tool_use":
            tool_calls.append({"name": block.name, "arguments": block.input})
    return {"text": "\n".join(text_parts), "tool_calls": tool_calls}


def call_openai(messages: list[dict], model: str, max_tokens: int = 1024) -> dict:
    try:
        from openai import OpenAI
    except ImportError:
        print("Install the openai SDK:  pip install openai", file=sys.stderr)
        sys.exit(1)
    client = OpenAI()
    resp = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens)
    choice = resp.choices[0]
    tool_calls = []
    if choice.message.tool_calls:
        for tc in choice.message.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except (json.JSONDecodeError, TypeError):
                args = tc.function.arguments
            tool_calls.append({"name": tc.function.name, "arguments": args})
    return {"text": choice.message.content or "", "tool_calls": tool_calls}


def _deterministic_wrong_letter(scenario: dict) -> str:
    """Pick a stable wrong letter for a scenario (for 'weak' mode).

    Hash the scenario id so results are reproducible across runs.
    """
    correct = (scenario.get("correct_answer") or "").strip().upper()
    sid = scenario.get("id", 0)
    h = int(hashlib.md5(str(sid).encode()).hexdigest(), 16)
    choices = [c for c in "ABCD" if c != correct] or list("ABCD")
    return choices[h % len(choices)]


def _deterministic_random_letter(scenario: dict) -> str:
    """Pick a deterministic pseudo-random letter keyed on scenario id.

    Using the scenario id as seed keeps the run reproducible while giving
    ~25% baseline accuracy across a balanced set.
    """
    sid = scenario.get("id", 0)
    rng = random.Random(sid)
    return rng.choice(list("ABCD"))


def call_mock(
    messages: list[dict],
    model: str,
    max_tokens: int = 1024,
    scenario: dict | None = None,
    mode: str = "perfect",
    mcq_scenario_for_judge: dict | None = None,
) -> dict:
    """Deterministic offline provider for CI and reproducibility.

    Behavior depends on the message shape and the `mode`:

    - Judge call (system prompt includes "impartial grader"): always returns
      ``VERDICT: PASS`` with evidence. This lets us test the open-ended
      pipeline end to end without hitting a real LLM. Weakness of the judge
      is out of scope for the mock — we want the pipeline's plumbing tested,
      not the judge's discernment.

    - Subject call for an MCQ scenario: returns the scenario's
      ``correct_answer`` letter (``perfect``), a wrong letter (``weak``), or
      a deterministic pseudo-random letter (``random``).

    - Subject call for a keyword scenario: returns text containing the
      expected keyword in ``perfect`` mode, an unrelated sentence in
      ``weak``/``random`` mode.

    - Subject call for an open-ended (rubric) scenario: joins all
      ``must_mention`` keywords into one sentence in ``perfect`` mode,
      emits a red flag in ``weak`` mode, or a vague sentence in ``random``.
    """
    # Detect judge calls by looking for the judge system prompt signature.
    for m in messages:
        if m.get("role") == "system" and "impartial grader" in m.get("content", ""):
            return {
                "text": (
                    "VERDICT: PASS\n"
                    "EVIDENCE: The response clearly addresses the rubric "
                    "items and cites the relevant workspace evidence.\n"
                    "MUST_MENTION_FOUND: all\n"
                    "RED_FLAGS_FOUND: none"
                ),
                "tool_calls": [],
            }

    mode = (mode or "perfect").lower()
    if mode not in {"perfect", "random", "weak"}:
        mode = "perfect"

    # No scenario context → we can't fake a targeted answer. Return something
    # that won't accidentally score as correct for any letter/keyword.
    if scenario is None:
        return {"text": "[mock] no scenario context provided", "tool_calls": []}

    # Open-ended scenarios have no 'scoring' field but carry a rubric.
    has_rubric = bool(scenario.get("rubric"))
    default_scoring = "rubric" if has_rubric else "mcq"
    scoring = scenario.get("scoring", default_scoring)
    if scoring == "mcq":
        correct = (scenario.get("correct_answer") or "").strip().upper()
        if mode == "perfect":
            letter = correct or "A"
        elif mode == "weak":
            letter = _deterministic_wrong_letter(scenario)
        else:  # random
            letter = _deterministic_random_letter(scenario)
        return {
            "text": f"{letter}. [mock:{mode}]",
            "tool_calls": [],
        }

    if scoring == "keyword":
        keyword = (scenario.get("correct_answer") or "").strip()
        if mode == "perfect":
            text = f"The answer is {keyword}. [mock:{mode}]" if keyword else "[mock]"
        else:
            text = "[mock] deliberately unhelpful response."
        return {"text": text, "tool_calls": []}

    # Open-ended / rubric scoring.
    rubric = scenario.get("rubric", {}) or {}
    must = rubric.get("must_mention", []) or []
    red_flags = rubric.get("red_flags", []) or []
    if mode == "perfect":
        # Emit every must_mention keyword so the automated rubric passes.
        body = (
            "Flagging the key concerns: "
            + ", ".join(must)
            + ". [mock:perfect]"
        )
        return {"text": body, "tool_calls": []}
    if mode == "weak":
        # Trigger a red flag if available, otherwise return a vacuous reply.
        rf = red_flags[0] if red_flags else "no issues here"
        return {"text": f"{rf}. [mock:weak]", "tool_calls": []}
    # random
    return {"text": "[mock:random] a generic noncommittal summary.", "tool_calls": []}


def dispatch(
    provider: str,
    messages: list[dict],
    model: str,
    max_tokens: int = 1024,
    scenario: dict | None = None,
    mock_mode: str = "perfect",
) -> dict:
    """Dispatch to an LLM provider.

    ``scenario`` and ``mock_mode`` are only consumed by the ``mock``
    provider; real providers ignore them. This lets the mock provider
    synthesize targeted responses without leaking test hooks into the
    production code path.
    """
    if provider == "anthropic":
        return call_anthropic(messages, model, max_tokens)
    if provider == "openai":
        return call_openai(messages, model, max_tokens)
    if provider == "mock":
        return call_mock(messages, model, max_tokens,
                         scenario=scenario, mode=mock_mode)
    return call_openai(messages, model, max_tokens)


# ---------------------------------------------------------------------------
# MCQ scoring
# ---------------------------------------------------------------------------

def extract_mcq_choice(text: str) -> str | None:
    """Extract the model's chosen letter from its response.

    Checks patterns in priority order to avoid false positives on text like
    "Not B. C is correct." or "B is tempting, but C is correct."
    """
    stripped = text.strip()

    # 1. Entire response is one letter.
    if len(stripped) == 1 and stripped.upper() in "ABCD":
        return stripped.upper()

    # 2. Explicit "answer is X" / "X is correct" / "X is right" / "X is the answer".
    m = re.search(
        r"(?:the\s+)?(?:correct\s+)?answer\s*(?:is|:)\s*\(?([A-Da-d])\)?",
        stripped, re.IGNORECASE,
    )
    if m:
        return m.group(1).upper()
    m = re.search(r"\b([A-Da-d])\s+is\s+(?:correct|right|the\s+(?:correct\s+)?answer)\b",
                  stripped, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # "ultimately, C is the answer" / "therefore, B"
    m = re.search(
        r"(?:ultimately|therefore|thus|hence|so)[,\s]+\(?([A-Da-d])\)?"
        r"(?:\b|\s+is\s+(?:correct|right|the\s+answer))",
        stripped, re.IGNORECASE,
    )
    if m:
        return m.group(1).upper()
    # "my answer: X" / "final answer: X"
    m = re.search(r"\b(?:my|final)\s+answer\s*:\s*\(?([A-Da-d])\)?",
                  stripped, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    # 3. "pick X" / "choose X" / "go with X" / "select X" / "option X".
    m = re.search(r"(?:pick|choose|go\s+with|select)\s+\(?([A-Da-d])\)?",
                  stripped, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.search(r"\boption\s+([A-Da-d])\b", stripped, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    # 4. Starts with letter + delimiter (period, paren, colon, dash, newline,
    #    "because", or end). Excludes "B is tempting" where the letter starts
    #    a sentence about the choice rather than selecting it.
    m = re.match(
        r"^\*{0,2}\(?([A-Da-d])\)?\*{0,2}\s*(?:[.):\-\u2014,]|\bbecause\b|\n|$)",
        stripped, re.IGNORECASE,
    )
    if m:
        return m.group(1).upper()

    # 5. Letter on its own line.
    for line in stripped.splitlines():
        line = line.strip()
        m = re.match(r"^\*{0,2}\(?([A-Da-d])\)?\*{0,2}[.):]*$", line)
        if m:
            return m.group(1).upper()

    return None


def score_mcq(scenario: dict, response: dict) -> dict:
    correct = scenario.get("correct_answer", "").strip().upper()
    chosen = extract_mcq_choice(response["text"])
    ok = (chosen == correct) if correct and len(correct) == 1 else False
    return {"correct": ok, "chosen": chosen, "expected": correct}


def score_keyword(scenario: dict, response: dict) -> dict:
    keyword = scenario.get("correct_answer", "").strip()
    ok = bool(keyword) and keyword.lower() in response["text"].lower()
    return {"correct": ok, "keyword": keyword,
            "found": keyword.lower() in response["text"].lower() if keyword else False}


# ---------------------------------------------------------------------------
# Open-ended: rubric + LLM-judge scoring
# ---------------------------------------------------------------------------

JUDGE_SYSTEM = (
    "You are an impartial grader evaluating a PM's response to a judgment "
    "scenario. Your job is to determine whether the response demonstrates "
    "that the PM caught the critical insight, according to a rubric. "
    "Be strict: a response that does the literal ask without noticing the "
    "deeper issue should FAIL. A response that catches the insight and "
    "communicates it appropriately should PASS."
)

JUDGE_TEMPLATE = """Scenario: {name}

The PM was given a workspace (engineering team context) and asked the following:
<trigger>
{trigger}
</trigger>

The PM responded:
<response>
{response}
</response>

Grading rubric:
- Must mention (ALL required, or clear paraphrase): {must_mention}
- Should mention (bonus signals): {should_mention}
- Red flags (these phrases indicate the PM missed the point): {red_flags}

Scenario-specific judge instructions:
{judge_prompt}

Grade the response.

Respond in this exact format:
VERDICT: PASS or FAIL
EVIDENCE: <1-2 sentences citing specific text from the response that supports your verdict>
MUST_MENTION_FOUND: <comma-separated list of which must_mention items were clearly addressed>
RED_FLAGS_FOUND: <comma-separated list of which red_flags appeared, or "none">
"""


def score_rubric_automated(scenario: dict, response: dict) -> dict:
    """Automated rubric pre-check: do must_mention keywords appear? Red flags?"""
    rubric = scenario.get("rubric", {})
    text = response["text"].lower()
    must = rubric.get("must_mention", [])
    red = rubric.get("red_flags", [])
    should = rubric.get("should_mention", [])

    must_hits = [kw for kw in must if kw.lower() in text]
    red_hits = [kw for kw in red if kw.lower() in text]
    should_hits = [kw for kw in should if kw.lower() in text]

    automated_pass = len(must_hits) == len(must) and not red_hits
    return {
        "automated_pass": automated_pass,
        "must_mention_hits": must_hits,
        "must_mention_missing": [kw for kw in must if kw.lower() not in text],
        "red_flag_hits": red_hits,
        "should_mention_hits": should_hits,
    }


def score_with_judge(scenario: dict, response: dict,
                     judge_provider: str, judge_model: str,
                     mock_mode: str = "perfect") -> dict:
    """Use an LLM judge to score the response against the rubric."""
    rubric = scenario.get("rubric", {})
    prompt = JUDGE_TEMPLATE.format(
        name=scenario.get("name", "?"),
        trigger=scenario["trigger"],
        response=response["text"],
        must_mention=", ".join(rubric.get("must_mention", [])),
        should_mention=", ".join(rubric.get("should_mention", [])),
        red_flags=", ".join(rubric.get("red_flags", [])),
        judge_prompt=scenario.get("judge_prompt", "Apply the rubric strictly."),
    )
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": prompt},
    ]
    try:
        judge_resp = dispatch(judge_provider, messages, judge_model,
                              max_tokens=500, scenario=scenario,
                              mock_mode=mock_mode)
    except Exception as e:
        return {"judge_error": str(e), "verdict": None}

    text = judge_resp["text"]
    m = re.search(r"VERDICT:\s*(PASS|FAIL)", text, re.IGNORECASE)
    verdict = m.group(1).upper() if m else None
    ev = re.search(r"EVIDENCE:\s*(.+?)(?:\n[A-Z_]+:|$)", text, re.DOTALL)
    evidence = ev.group(1).strip() if ev else ""
    return {
        "verdict": verdict,
        "evidence": evidence,
        "judge_text": text,
    }


def score_open_ended(scenario: dict, response: dict,
                     judge_provider: str, judge_model: str,
                     mock_mode: str = "perfect") -> dict:
    automated = score_rubric_automated(scenario, response)
    judged = score_with_judge(scenario, response, judge_provider, judge_model,
                              mock_mode=mock_mode)
    # Final score: judge verdict is authoritative when available.
    correct = (judged.get("verdict") == "PASS") if judged.get("verdict") else automated["automated_pass"]
    return {"correct": correct, "automated": automated, "judge": judged}


# ---------------------------------------------------------------------------
# Filtering and loading
# ---------------------------------------------------------------------------

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


def filter_scenarios_mcq(
    scenarios: list[dict],
    scenario_id: int | None,
    category: str | None,
    superhuman_only: bool,
) -> list[dict]:
    if scenario_id is not None:
        scenarios = [s for s in scenarios if s["id"] == scenario_id]
        if not scenarios:
            print(f"Scenario {scenario_id} not found.", file=sys.stderr)
            sys.exit(1)
    if superhuman_only:
        scenarios = [s for s in scenarios if s.get("category") == "Superhuman PM Judgment"]
    if category:
        scenarios = [s for s in scenarios if s.get("category", "").lower() == category.lower()]
        if not scenarios:
            print(f"Category '{category}' not found.", file=sys.stderr)
            sys.exit(1)
    before = len(scenarios)
    scenarios = [s for s in scenarios if s.get("scoring") != "tool_use"]
    skipped = before - len(scenarios)
    if skipped:
        print(f"(Excluding {skipped} tool_use scenario(s) — requires an agent harness)\n")
    return scenarios


def filter_scenarios_open(
    scenarios: list[dict],
    scenario_id: int | None,
) -> list[dict]:
    if scenario_id is not None:
        scenarios = [s for s in scenarios if s["id"] == scenario_id]
        if not scenarios:
            print(f"Open-ended scenario {scenario_id} not found.", file=sys.stderr)
            sys.exit(1)
    return scenarios


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save_results(results: list[dict], model: str, provider: str, mode: str) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    safe_model = re.sub(r"[^a-zA-Z0-9_\-.]", "_", model)
    out_path = RESULTS_DIR / f"{ts}_{mode}_{provider}_{safe_model}.json"
    summary = {
        "timestamp": ts, "mode": mode, "provider": provider, "model": model,
        "total": len(results),
        "correct": sum(1 for r in results if r.get("correct")),
        "scenarios": results,
    }
    out_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return out_path


def print_scorecard(results: list[dict], model: str, mode: str) -> None:
    categories: dict[str, list[bool]] = {}
    for r in results:
        categories.setdefault(r.get("category", "?"), []).append(r.get("correct", False))
    header = f"PM-Bench {mode.upper()} Results -- {model}"
    print(f"\n{header}")
    print("=" * len(header))
    print(f"{'Category':<40} {'Score':>8}  {'Pct':>7}")
    print("-" * 60)
    total_c, total_n = 0, 0
    for cat, scores in categories.items():
        c, n = sum(scores), len(scores)
        total_c += c; total_n += n
        print(f"{cat:<40} {c:>3}/{n:<4} {c/n*100 if n else 0:>6.1f}%")
    print("-" * 60)
    print(f"{'TOTAL':<40} {total_c:>3}/{total_n:<4} {total_c/total_n*100 if total_n else 0:>6.1f}%")
    print()


# ---------------------------------------------------------------------------
# Runners
# ---------------------------------------------------------------------------

def run_mcq(args, scenarios: list[dict]) -> list[dict]:
    results: list[dict] = []
    for i, scenario in enumerate(scenarios, 1):
        sid = scenario["id"]
        name = scenario.get("name", str(sid))
        cat = scenario.get("category", "?")
        scoring = scenario.get("scoring", "mcq")
        print(f"[{i}/{len(scenarios)}] #{sid} {name}  ({cat}, {scoring})")

        context = build_context(scenario)
        messages = build_messages(scenario, context, MCQ_SYSTEM)

        if args.dry_run:
            print(f"  trigger: {scenario['trigger'][:120]}")
            print(f"  answer:  {scenario.get('correct_answer', '(none)')}")
            results.append({"id": sid, "name": name, "category": cat,
                            "scoring": scoring, "correct": False, "dry_run": True})
            continue

        try:
            response = dispatch(
                args.provider, messages, args.model,
                scenario=scenario,
                mock_mode=getattr(args, "mock_mode", "perfect"),
            )
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"id": sid, "name": name, "category": cat,
                            "scoring": scoring, "correct": False, "error": str(e)})
            continue

        if scoring == "mcq":
            score = score_mcq(scenario, response)
        else:
            score = score_keyword(scenario, response)

        correct = score["correct"]
        preview = response["text"][:90].replace("\n", " ") if response["text"] else "(empty)"
        print(f"  {'PASS' if correct else 'FAIL'}  -> {preview}")

        results.append({
            "id": sid, "name": name, "category": cat, "scoring": scoring,
            "correct": correct, "response_text": response["text"],
            "score_detail": score,
        })
        if i < len(scenarios) and args.provider != "mock":
            time.sleep(0.5)
    return results


def run_open_ended(args, scenarios: list[dict]) -> list[dict]:
    judge_provider = args.judge_provider or args.provider
    if args.judge_model:
        judge_model = args.judge_model
    elif judge_provider == "anthropic":
        judge_model = "claude-sonnet-4-20250514"
    elif judge_provider == "mock":
        judge_model = f"mock-{getattr(args, 'mock_mode', 'perfect')}-judge"
    else:
        judge_model = "gpt-4o"
    print(f"Subject: {args.provider}/{args.model}  |  Judge: {judge_provider}/{judge_model}\n")

    results: list[dict] = []
    for i, scenario in enumerate(scenarios, 1):
        sid = scenario["id"]
        name = scenario.get("name", str(sid))
        cat = scenario.get("category", "?")
        print(f"[{i}/{len(scenarios)}] #{sid} {name}  ({cat}, open-ended)")

        context = build_context(scenario)
        messages = build_messages(scenario, context, OPEN_ENDED_SYSTEM)

        if args.dry_run:
            print(f"  trigger: {scenario['trigger'][:120]}")
            rubric = scenario.get("rubric", {})
            print(f"  must:    {rubric.get('must_mention')}")
            results.append({"id": sid, "name": name, "category": cat,
                            "correct": False, "dry_run": True})
            continue

        try:
            response = dispatch(
                args.provider, messages, args.model, max_tokens=1500,
                scenario=scenario,
                mock_mode=getattr(args, "mock_mode", "perfect"),
            )
        except Exception as e:
            print(f"  ERROR (subject): {e}")
            results.append({"id": sid, "name": name, "category": cat,
                            "correct": False, "error": str(e)})
            continue

        score = score_open_ended(
            scenario, response, judge_provider, judge_model,
            mock_mode=getattr(args, "mock_mode", "perfect"),
        )
        correct = score["correct"]
        preview = response["text"][:90].replace("\n", " ") if response["text"] else "(empty)"
        auto = score["automated"]
        judge = score["judge"]
        judge_verdict = judge.get("verdict") or "?"
        auto_pass = "Y" if auto["automated_pass"] else "N"
        print(f"  {'PASS' if correct else 'FAIL'}  judge={judge_verdict} auto={auto_pass}  -> {preview}")

        results.append({
            "id": sid, "name": name, "category": cat, "scoring": "open-ended",
            "correct": correct, "response_text": response["text"],
            "score_detail": score,
        })
        if i < len(scenarios) and args.provider != "mock":
            time.sleep(0.5)
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="PM-Bench: Evaluate AI models on PM judgment scenarios.")
    parser.add_argument("--mode", choices=["mcq", "open-ended"], default="mcq",
                        help="Evaluation mode (default: mcq)")
    parser.add_argument("--provider", choices=["anthropic", "openai", "mock"], default="anthropic",
                        help="LLM provider. 'mock' runs end-to-end with no API key.")
    parser.add_argument("--mock-mode", choices=["perfect", "random", "weak"], default="perfect",
                        help="Mock provider behavior: perfect (100%% correct), "
                             "random (~25%% on MCQ), or weak (0%% correct).")
    parser.add_argument("--model", type=str, default=None,
                        help="Model override (default: claude-sonnet-4-20250514 / gpt-4o)")
    parser.add_argument("--judge-provider", choices=["anthropic", "openai", "mock"], default=None,
                        help="Provider for judge model in open-ended mode")
    parser.add_argument("--judge-model", type=str, default=None,
                        help="Judge model (open-ended mode). Default matches --provider.")
    parser.add_argument("--scenario", type=int, default=None, help="Run a single scenario by ID")
    parser.add_argument("--category", type=str, default=None, help='MCQ only: run one category')
    parser.add_argument("--superhuman-only", action="store_true",
                        help="MCQ only: run only Superhuman PM Judgment (20 MCQ)")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts without calling the API")
    args = parser.parse_args()

    if args.model is None:
        if args.provider == "anthropic":
            args.model = "claude-sonnet-4-20250514"
        elif args.provider == "mock":
            args.model = f"mock-{args.mock_mode}"
        else:
            args.model = "gpt-4o"

    if args.mode == "mcq":
        all_scenarios = load_scenarios(SCENARIOS_FILE)
        scenarios = filter_scenarios_mcq(all_scenarios, args.scenario, args.category,
                                          args.superhuman_only)
    else:
        all_scenarios = load_scenarios(OPEN_ENDED_FILE)
        scenarios = filter_scenarios_open(all_scenarios, args.scenario)

    if not scenarios:
        print("No scorable scenarios to run.", file=sys.stderr)
        sys.exit(1)

    print(f"PM-Bench  |  mode={args.mode}  provider={args.provider}  model={args.model}")
    print(f"Running {len(scenarios)} scenario(s)...\n")

    if args.mode == "mcq":
        results = run_mcq(args, scenarios)
    else:
        results = run_open_ended(args, scenarios)

    print_scorecard(results, args.model, args.mode)

    if not args.dry_run:
        out_path = save_results(results, args.model, args.provider, args.mode)
        print(f"Results saved to: {out_path}")


if __name__ == "__main__":
    main()
