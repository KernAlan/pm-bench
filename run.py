#!/usr/bin/env python3
"""
PM-Bench Evaluation Runner

Runs scenarios from scenarios/scenarios.json against an LLM and scores responses.

Usage:
    python run.py                                # Run all scorable scenarios
    python run.py --provider openai --model gpt-4o
    python run.py --superhuman-only              # Run only Superhuman PM Judgment (20)
    python run.py --category "Memory Recall"     # Run one category
    python run.py --scenario 49                  # Run a single scenario by numeric ID
    python run.py --dry-run                      # Print prompts, don't call the API

Notes:
    - "mcq" and "keyword" scenarios are fully automated.
    - "tool_use" scenarios are always excluded. This runner does not send tool
      schemas to the model, so tool calls cannot occur and scoring would be
      meaningless. Use tool_use scenarios as integration tests in your own
      agent harness instead.
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
SCENARIOS_FILE = ROOT / "scenarios" / "scenarios.json"
FIXTURES_DIR = ROOT / "fixtures"
RESULTS_DIR = ROOT / "results"

# ---------------------------------------------------------------------------
# Context resolution
# ---------------------------------------------------------------------------

def resolve_ref(ref: str) -> str:
    """If *ref* starts with @fixtures/, load file content; otherwise return as-is."""
    if ref.startswith("@fixtures/"):
        path = FIXTURES_DIR / ref[len("@fixtures/"):]
        if not path.exists():
            print(f"  [warn] fixture not found: {path}", file=sys.stderr)
            return ""
        return path.read_text(encoding="utf-8")
    return ref  # inline content


def build_context(scenario: dict) -> str:
    """Assemble all workspace_files into a single context string."""
    parts: list[str] = []
    for filename, content_or_ref in scenario.get("workspace_files", {}).items():
        content = resolve_ref(content_or_ref)
        if content:
            parts.append(f"--- {filename} ---\n{content}")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are the acting PM for this team. "
    "Use the workspace context provided to answer the question. "
    "For multiple-choice questions, respond with the correct letter "
    "(A, B, C, or D) and a brief explanation. "
    "Be concise and specific."
)


def build_messages(scenario: dict, context: str) -> list[dict]:
    """Return a message list suitable for chat-completion APIs."""
    user_content = ""
    if context:
        user_content += f"<workspace>\n{context}\n</workspace>\n\n"
    user_content += scenario["trigger"]
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


# ---------------------------------------------------------------------------
# LLM clients
# ---------------------------------------------------------------------------

def call_anthropic(messages: list[dict], model: str) -> dict:
    """Call the Anthropic Messages API. Returns {text, tool_calls}."""
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

    kwargs: dict[str, Any] = dict(
        model=model, max_tokens=1024, messages=chat_messages,
    )
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


def call_openai(messages: list[dict], model: str) -> dict:
    """Call the OpenAI Chat Completions API. Returns {text, tool_calls}."""
    try:
        from openai import OpenAI
    except ImportError:
        print("Install the openai SDK:  pip install openai", file=sys.stderr)
        sys.exit(1)

    client = OpenAI()
    resp = client.chat.completions.create(model=model, messages=messages, max_tokens=1024)
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


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def extract_mcq_choice(text: str) -> str | None:
    """Extract the model's chosen letter from its response.

    Designed to avoid false positives: "Not B. C is correct." must NOT
    return B, and "B is tempting, but C is correct." must return C.

    Strategy: check high-confidence patterns first, fall back carefully.
    All matching is case-insensitive.
    """
    stripped = text.strip()

    # 1. Entire response is one letter.
    if len(stripped) == 1 and stripped.upper() in "ABCD":
        return stripped.upper()

    # 2. Explicit "answer is X" / "correct answer is X" / "X is correct"
    #    These are the strongest signals of a chosen answer.
    m = re.search(
        r"(?:the\s+)?(?:correct\s+)?answer\s*(?:is|:)\s*\(?([A-Da-d])\)?",
        stripped, re.IGNORECASE,
    )
    if m:
        return m.group(1).upper()
    m = re.search(r"\b([A-Da-d])\s+is\s+correct\b", stripped, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    # 3. "I would pick C", "Option C", "go with B", "select A"
    m = re.search(
        r"(?:pick|choose|go\s+with|select)\s+\(?([A-Da-d])\)?",
        stripped, re.IGNORECASE,
    )
    if m:
        return m.group(1).upper()
    m = re.search(r"\boption\s+([A-Da-d])\b", stripped, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    # 4. Starts with letter + delimiter or "because" / explanation connector.
    #    Matches: "B.", "B)", "B:", "B —", "B,", "C because", "(C) because"
    #    Excludes: "B is tempting" (letter starts a sentence about the choice).
    m = re.match(
        r"^\*{0,2}\(?([A-Da-d])\)?\*{0,2}\s*(?:[.):\-\u2014,]|\bbecause\b|\n|$)",
        stripped, re.IGNORECASE,
    )
    if m:
        return m.group(1).upper()

    # 5. Letter on its own line (e.g. model outputs "B\n\nExplanation...").
    for line in stripped.splitlines():
        line = line.strip()
        m = re.match(r"^\*{0,2}\(?([A-Da-d])\)?\*{0,2}[.):]*$", line)
        if m:
            return m.group(1).upper()

    return None


def score_mcq(scenario: dict, response: dict) -> bool:
    """Check if the model's chosen answer matches the correct one."""
    correct = scenario.get("correct_answer", "").strip().upper()
    if not correct or len(correct) != 1:
        return False
    chosen = extract_mcq_choice(response["text"])
    return chosen == correct


def score_keyword(scenario: dict, response: dict) -> bool:
    """Check if the response contains the required keyword from correct_answer."""
    keyword = scenario.get("correct_answer", "").strip()
    if not keyword:
        return False
    return keyword.lower() in response["text"].lower()


def score_scenario(scenario: dict, response: dict) -> bool:
    scoring = scenario.get("scoring", "mcq")
    if scoring == "mcq":
        return score_mcq(scenario, response)
    elif scoring == "keyword":
        return score_keyword(scenario, response)
    # tool_use scenarios are filtered out before reaching the scorer.
    return False


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save_results(results: list[dict], model: str, provider: str) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    safe_model = re.sub(r"[^a-zA-Z0-9_\-.]", "_", model)
    out_path = RESULTS_DIR / f"{ts}_{provider}_{safe_model}.json"
    summary = {
        "timestamp": ts, "provider": provider, "model": model,
        "total": len(results),
        "correct": sum(1 for r in results if r["correct"]),
        "scenarios": results,
    }
    out_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return out_path


def print_scorecard(results: list[dict], model: str) -> None:
    categories: dict[str, list[bool]] = {}
    for r in results:
        categories.setdefault(r.get("category", "?"), []).append(r["correct"])
    header = f"PM-Bench Results -- {model}"
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
# Main
# ---------------------------------------------------------------------------

def load_scenarios() -> list[dict]:
    if not SCENARIOS_FILE.exists():
        print(f"Scenarios file not found: {SCENARIOS_FILE}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(SCENARIOS_FILE.read_text(encoding="utf-8"))
    # The file has a top-level object with a "scenarios" array.
    if isinstance(data, dict) and "scenarios" in data:
        return data["scenarios"]
    if isinstance(data, list):
        return data
    print("Unexpected scenarios.json format.", file=sys.stderr)
    sys.exit(1)


def filter_scenarios(
    scenarios: list[dict],
    scenario_id: int | None,
    category: str | None,
    superhuman_only: bool,
) -> list[dict]:
    # Apply content filters first.
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

    # Always exclude tool_use scenarios — this runner sends no tool schemas,
    # so tool calls cannot occur and scoring would be meaningless.
    before = len(scenarios)
    scenarios = [s for s in scenarios if s.get("scoring") != "tool_use"]
    skipped = before - len(scenarios)
    if skipped:
        print(f"(Excluding {skipped} tool_use scenario(s) — requires an agent harness with tool definitions)\n")

    return scenarios


def main() -> None:
    parser = argparse.ArgumentParser(description="PM-Bench: Evaluate AI models on PM judgment scenarios.")
    parser.add_argument("--provider", choices=["anthropic", "openai"], default="anthropic")
    parser.add_argument("--model", type=str, default=None,
                        help="Model override (default: claude-sonnet-4-20250514 / gpt-4o)")
    parser.add_argument("--scenario", type=int, default=None, help="Run a single scenario by numeric ID (e.g., 49)")
    parser.add_argument("--category", type=str, default=None, help='Run a category (e.g., "Memory Recall")')
    parser.add_argument("--superhuman-only", action="store_true", help="Run only Superhuman PM Judgment (20 MCQ)")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts without calling the API")
    args = parser.parse_args()

    if args.model is None:
        args.model = "claude-sonnet-4-20250514" if args.provider == "anthropic" else "gpt-4o"

    all_scenarios = load_scenarios()
    scenarios = filter_scenarios(all_scenarios, args.scenario, args.category,
                                args.superhuman_only)

    if not scenarios:
        print("No scorable scenarios to run. (tool_use scenarios require an external harness)", file=sys.stderr)
        sys.exit(1)

    print(f"PM-Bench  |  provider={args.provider}  model={args.model}")
    print(f"Running {len(scenarios)} scenario(s)...\n")

    call_fn = call_anthropic if args.provider == "anthropic" else call_openai
    results: list[dict] = []

    for i, scenario in enumerate(scenarios, 1):
        sid = scenario["id"]
        name = scenario.get("name", str(sid))
        cat = scenario.get("category", "?")
        scoring = scenario.get("scoring", "mcq")
        print(f"[{i}/{len(scenarios)}] #{sid} {name}  ({cat}, {scoring})")

        context = build_context(scenario)
        messages = build_messages(scenario, context)

        if args.dry_run:
            print(f"  system: {messages[0]['content'][:80]}...")
            trigger_preview = scenario['trigger'][:120].replace('\n', ' ')
            print(f"  trigger: {trigger_preview}...")
            print(f"  answer: {scenario.get('correct_answer', '(none)')}")
            results.append({"id": sid, "name": name, "category": cat,
                            "scoring": scoring, "correct": False, "response": "(dry run)"})
            continue

        try:
            response = call_fn(messages, args.model)
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"id": sid, "name": name, "category": cat,
                            "scoring": scoring, "correct": False, "error": str(e)})
            continue

        correct = score_scenario(scenario, response)
        status = "PASS" if correct else "FAIL"
        preview = response["text"][:100].replace("\n", " ") if response["text"] else "(no text)"
        print(f"  {status}  -> {preview}")

        results.append({"id": sid, "name": name, "category": cat, "scoring": scoring,
                        "correct": correct, "response_text": response["text"],
                        "tool_calls": response["tool_calls"]})

        if i < len(scenarios):
            time.sleep(0.5)

    print_scorecard(results, args.model)

    if not args.dry_run:
        out_path = save_results(results, args.model, args.provider)
        print(f"Results saved to: {out_path}")


if __name__ == "__main__":
    main()
