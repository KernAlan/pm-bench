#!/usr/bin/env python3
"""
PM-Bench Evaluation Runner

Loads scenarios from scenarios/scenarios.json, assembles context from workspace
and fixture files, calls an LLM, scores the response, and prints a scorecard.

Usage:
    python run.py                                # Run all scenarios with Anthropic
    python run.py --provider openai --model gpt-4o
    python run.py --superhuman-only              # Run only Superhuman PM Judgment
    python run.py --category "Memory Recall"     # Run one category
    python run.py --scenario S01                 # Run a single scenario by ID
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
WORKSPACE_DIR = ROOT / "workspace"
RESULTS_DIR = ROOT / "results"

# ---------------------------------------------------------------------------
# Fixture & workspace resolution
# ---------------------------------------------------------------------------

def load_fixture(ref: str) -> str:
    """Resolve a @fixtures/ or @workspace/ reference to file content."""
    if ref.startswith("@fixtures/"):
        path = FIXTURES_DIR / ref[len("@fixtures/"):]
    elif ref.startswith("@workspace/"):
        path = WORKSPACE_DIR / ref[len("@workspace/"):]
    else:
        path = ROOT / ref
    if not path.exists():
        print(f"  [warn] fixture not found: {path}", file=sys.stderr)
        return ""
    return path.read_text(encoding="utf-8")


def resolve_context(scenario: dict) -> str:
    """
    Build the full context string for a scenario.

    Each scenario may declare:
      - "context_files": list of @fixtures/... or @workspace/... refs
      - "context_inline": a literal string block
      - "workspace": true  -> include all core workspace files
    """
    parts: list[str] = []

    # If the scenario requests the full workspace, include core files.
    if scenario.get("workspace", False):
        for name in ("IDENTITY.md", "INTENTS.md", "MEMORY.md", "HEARTBEAT.md"):
            ws_file = WORKSPACE_DIR / name
            if ws_file.exists():
                parts.append(f"--- {name} ---\n{ws_file.read_text(encoding='utf-8')}")

        # Include logs
        logs_dir = WORKSPACE_DIR / "logs"
        if logs_dir.is_dir():
            for log_file in sorted(logs_dir.iterdir()):
                if log_file.suffix == ".md":
                    parts.append(
                        f"--- logs/{log_file.name} ---\n"
                        f"{log_file.read_text(encoding='utf-8')}"
                    )

        # Include memory files
        mem_dir = WORKSPACE_DIR / "memory"
        if mem_dir.is_dir():
            for mem_file in sorted(mem_dir.iterdir()):
                if mem_file.suffix == ".md":
                    parts.append(
                        f"--- memory/{mem_file.name} ---\n"
                        f"{mem_file.read_text(encoding='utf-8')}"
                    )

    # Explicit context files
    for ref in scenario.get("context_files", []):
        content = load_fixture(ref)
        if content:
            label = ref.split("/")[-1]
            parts.append(f"--- {label} ---\n{content}")

    # Inline context
    if scenario.get("context_inline"):
        parts.append(scenario["context_inline"])

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------

def build_messages(scenario: dict, context: str) -> list[dict]:
    """Return a message list suitable for chat-completion APIs."""
    system = scenario.get(
        "system_prompt",
        (
            "You are the acting PM for Acme Corp's Platform Team. "
            "Use the workspace context provided to answer the question. "
            "Be concise and specific."
        ),
    )

    user_content = ""
    if context:
        user_content += f"<workspace>\n{context}\n</workspace>\n\n"
    user_content += scenario["prompt"]

    # For MCQ scenarios, append the choices.
    if scenario.get("scoring") == "mcq" and "choices" in scenario:
        user_content += "\n\nChoices:\n"
        for letter, text in scenario["choices"].items():
            user_content += f"  {letter}) {text}\n"
        user_content += (
            "\nRespond with ONLY the letter of the correct answer (A, B, C, or D)."
        )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]


def build_tools(scenario: dict) -> list[dict] | None:
    """If the scenario defines available tools, return them in OpenAI format."""
    if "tools" not in scenario:
        return None
    return scenario["tools"]


# ---------------------------------------------------------------------------
# LLM clients
# ---------------------------------------------------------------------------

def call_anthropic(
    messages: list[dict],
    model: str,
    tools: list[dict] | None = None,
) -> dict:
    """Call the Anthropic Messages API. Returns {text, tool_calls, raw}."""
    try:
        from anthropic import Anthropic
    except ImportError:
        print("Install the anthropic SDK:  pip install anthropic", file=sys.stderr)
        sys.exit(1)

    client = Anthropic()

    # Separate system from messages for Anthropic's API.
    system_text = ""
    chat_messages = []
    for m in messages:
        if m["role"] == "system":
            system_text += m["content"] + "\n"
        else:
            chat_messages.append(m)

    kwargs: dict[str, Any] = dict(
        model=model,
        max_tokens=1024,
        messages=chat_messages,
    )
    if system_text.strip():
        kwargs["system"] = system_text.strip()

    if tools:
        # Convert OpenAI-style tool defs to Anthropic format.
        anthropic_tools = []
        for t in tools:
            if t.get("type") == "function":
                fn = t["function"]
                anthropic_tools.append({
                    "name": fn["name"],
                    "description": fn.get("description", ""),
                    "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
                })
            else:
                anthropic_tools.append(t)
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

    resp = client.messages.create(**kwargs)

    text_parts = []
    tool_calls = []
    for block in resp.content:
        if block.type == "text":
            text_parts.append(block.text)
        elif block.type == "tool_use":
            tool_calls.append({
                "name": block.name,
                "arguments": block.input,
            })

    return {
        "text": "\n".join(text_parts),
        "tool_calls": tool_calls,
        "raw": resp.model_dump() if hasattr(resp, "model_dump") else str(resp),
    }


def call_openai(
    messages: list[dict],
    model: str,
    tools: list[dict] | None = None,
) -> dict:
    """Call the OpenAI Chat Completions API. Returns {text, tool_calls, raw}."""
    try:
        from openai import OpenAI
    except ImportError:
        print("Install the openai SDK:  pip install openai", file=sys.stderr)
        sys.exit(1)

    client = OpenAI()

    kwargs: dict[str, Any] = dict(
        model=model,
        messages=messages,
        max_tokens=1024,
    )
    if tools:
        kwargs["tools"] = tools

    resp = client.chat.completions.create(**kwargs)
    choice = resp.choices[0]

    tool_calls = []
    if choice.message.tool_calls:
        for tc in choice.message.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except (json.JSONDecodeError, TypeError):
                args = tc.function.arguments
            tool_calls.append({
                "name": tc.function.name,
                "arguments": args,
            })

    return {
        "text": choice.message.content or "",
        "tool_calls": tool_calls,
        "raw": resp.model_dump() if hasattr(resp, "model_dump") else str(resp),
    }


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_mcq(scenario: dict, response: dict) -> bool:
    """Check if the model's text response contains the correct answer letter."""
    correct = scenario.get("answer", "").strip().upper()
    if not correct:
        return False

    text = response["text"].strip().upper()

    # Check for the letter appearing as the first non-whitespace character,
    # or as a standalone word.
    # Common patterns: "B", "The answer is B", "(B)", "B)"
    if text == correct:
        return True
    if re.search(rf"\b{re.escape(correct)}\b", text):
        return True
    if text.startswith(correct):
        return True
    return False


def score_keyword(scenario: dict, response: dict) -> bool:
    """Check if the model's response contains the required keyword(s)."""
    keywords = scenario.get("keywords", [])
    if isinstance(keywords, str):
        keywords = [keywords]
    text = response["text"].lower()
    return all(kw.lower() in text for kw in keywords)


def score_tool_use(scenario: dict, response: dict) -> bool:
    """Check if the model called the expected tool with expected arguments."""
    expected = scenario.get("expected_tool", {})
    expected_name = expected.get("name", "")
    expected_args = expected.get("arguments", {})

    for tc in response.get("tool_calls", []):
        if tc["name"] == expected_name:
            # If specific arguments are required, check them.
            if expected_args:
                actual_args = tc.get("arguments", {})
                match = all(
                    str(actual_args.get(k, "")).lower() == str(v).lower()
                    for k, v in expected_args.items()
                )
                if match:
                    return True
            else:
                # Tool name match is sufficient.
                return True
    return False


def score_scenario(scenario: dict, response: dict) -> bool:
    """Score a scenario based on its scoring type."""
    scoring = scenario.get("scoring", "mcq")
    if scoring == "mcq":
        return score_mcq(scenario, response)
    elif scoring == "keyword":
        return score_keyword(scenario, response)
    elif scoring == "tool_use":
        return score_tool_use(scenario, response)
    else:
        print(f"  [warn] unknown scoring type: {scoring}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

def save_results(
    results: list[dict],
    model: str,
    provider: str,
) -> Path:
    """Save detailed results to a JSON file in results/."""
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    safe_model = re.sub(r"[^a-zA-Z0-9_\-.]", "_", model)
    out_path = RESULTS_DIR / f"{ts}_{provider}_{safe_model}.json"

    summary = {
        "timestamp": ts,
        "provider": provider,
        "model": model,
        "total": len(results),
        "correct": sum(1 for r in results if r["correct"]),
        "scenarios": results,
    }
    out_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return out_path


def print_scorecard(results: list[dict], model: str) -> None:
    """Print a formatted scorecard to stdout."""
    # Group by category.
    categories: dict[str, list[bool]] = {}
    for r in results:
        cat = r.get("category", "Unknown")
        categories.setdefault(cat, []).append(r["correct"])

    header = f"PM-Bench Results -- {model}"
    print(f"\n{header}")
    print("=" * len(header))
    print(f"{'Category':<40} {'Score':>8}  {'Pct':>7}")
    print("-" * 60)

    total_correct = 0
    total_count = 0
    for cat, scores in categories.items():
        correct = sum(scores)
        count = len(scores)
        total_correct += correct
        total_count += count
        pct = (correct / count * 100) if count else 0
        print(f"{cat:<40} {correct:>3}/{count:<4} {pct:>6.1f}%")

    print("-" * 60)
    pct = (total_correct / total_count * 100) if total_count else 0
    print(f"{'TOTAL':<40} {total_correct:>3}/{total_count:<4} {pct:>6.1f}%")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_scenarios() -> list[dict]:
    """Load scenarios from the JSON file."""
    if not SCENARIOS_FILE.exists():
        print(
            f"Scenarios file not found: {SCENARIOS_FILE}\n"
            "Create scenarios/scenarios.json with your scenario definitions.",
            file=sys.stderr,
        )
        sys.exit(1)
    return json.loads(SCENARIOS_FILE.read_text(encoding="utf-8"))


def filter_scenarios(
    scenarios: list[dict],
    scenario_id: str | None,
    category: str | None,
    superhuman_only: bool,
) -> list[dict]:
    """Filter scenarios based on CLI arguments."""
    if scenario_id:
        matches = [s for s in scenarios if s["id"] == scenario_id]
        if not matches:
            print(f"Scenario '{scenario_id}' not found.", file=sys.stderr)
            sys.exit(1)
        return matches

    if superhuman_only:
        return [
            s for s in scenarios
            if s.get("category", "").lower().startswith("superhuman")
            or s.get("category", "") == "Superhuman PM Judgment"
        ]

    if category:
        matches = [
            s for s in scenarios
            if s.get("category", "").lower() == category.lower()
        ]
        if not matches:
            print(f"Category '{category}' not found.", file=sys.stderr)
            cats = sorted(set(s.get("category", "") for s in scenarios))
            print(f"Available categories: {', '.join(cats)}", file=sys.stderr)
            sys.exit(1)
        return matches

    return scenarios


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PM-Bench: Evaluate AI models on product management scenarios.",
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai"],
        default="anthropic",
        help="LLM provider (default: anthropic)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name override (default: claude-sonnet-4-20250514 for Anthropic, gpt-4o for OpenAI)",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Run a specific scenario by ID (e.g., S01)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help='Run all scenarios in a category (e.g., "Memory Recall")',
    )
    parser.add_argument(
        "--superhuman-only",
        action="store_true",
        help="Run only the 20 Superhuman PM Judgment scenarios",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompts without calling the API",
    )
    args = parser.parse_args()

    # Defaults
    if args.model is None:
        args.model = (
            "claude-sonnet-4-20250514" if args.provider == "anthropic" else "gpt-4o"
        )

    # Load and filter
    scenarios = load_scenarios()
    scenarios = filter_scenarios(
        scenarios, args.scenario, args.category, args.superhuman_only
    )

    print(f"PM-Bench  |  provider={args.provider}  model={args.model}")
    print(f"Running {len(scenarios)} scenario(s)...\n")

    call_fn = call_anthropic if args.provider == "anthropic" else call_openai
    results: list[dict] = []

    for i, scenario in enumerate(scenarios, 1):
        sid = scenario["id"]
        name = scenario.get("name", sid)
        category = scenario.get("category", "Unknown")
        scoring = scenario.get("scoring", "mcq")

        print(f"[{i}/{len(scenarios)}] {sid}: {name}  ({category}, {scoring})")

        # Build context and messages
        context = resolve_context(scenario)
        messages = build_messages(scenario, context)
        tools = build_tools(scenario)

        if args.dry_run:
            print(f"  system: {messages[0]['content'][:80]}...")
            print(f"  user:   {messages[1]['content'][:120]}...")
            if tools:
                print(f"  tools:  {[t.get('function', {}).get('name', t.get('name', '?')) for t in tools]}")
            results.append({
                "id": sid,
                "name": name,
                "category": category,
                "scoring": scoring,
                "correct": False,
                "response": "(dry run)",
            })
            continue

        # Call the model
        try:
            response = call_fn(messages, args.model, tools)
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                "id": sid,
                "name": name,
                "category": category,
                "scoring": scoring,
                "correct": False,
                "error": str(e),
                "response": None,
            })
            continue

        # Score
        correct = score_scenario(scenario, response)
        status = "PASS" if correct else "FAIL"
        print(f"  {status}", end="")
        if response["text"]:
            preview = response["text"][:100].replace("\n", " ")
            print(f"  -> {preview}")
        elif response["tool_calls"]:
            tc = response["tool_calls"][0]
            print(f"  -> tool: {tc['name']}({json.dumps(tc['arguments'], default=str)[:80]})")
        else:
            print()

        results.append({
            "id": sid,
            "name": name,
            "category": category,
            "scoring": scoring,
            "correct": correct,
            "response_text": response["text"],
            "tool_calls": response["tool_calls"],
        })

        # Be polite to rate limits.
        if i < len(scenarios):
            time.sleep(0.5)

    # Print scorecard
    print_scorecard(results, args.model)

    # Save results
    if not args.dry_run:
        out_path = save_results(results, args.model, args.provider)
        print(f"Results saved to: {out_path}")


if __name__ == "__main__":
    main()
