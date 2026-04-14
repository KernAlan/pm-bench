#!/usr/bin/env python3
"""PM-Bench offline demo.

Shows what PM-Bench evaluates without requiring any API keys. Loads the real
scenario data, walks through three representative scenarios (Memory Recall,
Superhuman PM Judgment MCQ, and the matched Open-Ended variant), prints the
trigger and workspace context a model would see, shows a hardcoded "strong
model" response, and scores it using the same functions the real runner uses.

Usage:
    python demo.py              # colorized output
    python demo.py --no-color   # plain text (pipes, logs, non-TTY)

To actually evaluate a model, set ANTHROPIC_API_KEY or OPENAI_API_KEY and run:
    python run.py --model claude-sonnet-4-5 --mode mcq
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCENARIOS_FILE = ROOT / "scenarios" / "scenarios.json"
OPEN_ENDED_FILE = ROOT / "scenarios" / "open-ended.json"
FIXTURES_DIR = ROOT / "fixtures"


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

class Style:
    """ANSI styling. All methods become no-ops when use_color is False."""

    def __init__(self, use_color: bool) -> None:
        self.use_color = use_color

    def bold(self, s: str) -> str:
        return f"\033[1m{s}\033[0m" if self.use_color else s

    def dim(self, s: str) -> str:
        return f"\033[2m{s}\033[0m" if self.use_color else s

    def green(self, s: str) -> str:
        return f"\033[32m{s}\033[0m" if self.use_color else s

    def red(self, s: str) -> str:
        return f"\033[31m{s}\033[0m" if self.use_color else s

    def cyan(self, s: str) -> str:
        return f"\033[36m{s}\033[0m" if self.use_color else s

    def yellow(self, s: str) -> str:
        return f"\033[33m{s}\033[0m" if self.use_color else s


# ---------------------------------------------------------------------------
# Data loading (mirrors run.py)
# ---------------------------------------------------------------------------

def resolve_ref(ref: str) -> str:
    """Resolve a workspace_files value. Strings starting with @fixtures/ are
    loaded from the fixtures/ dir; anything else is returned as-is."""
    if isinstance(ref, str) and ref.startswith("@fixtures/"):
        path = FIXTURES_DIR / ref[len("@fixtures/"):]
        if not path.exists():
            return f"[missing fixture: {path.name}]"
        return path.read_text(encoding="utf-8")
    return ref if isinstance(ref, str) else ""


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Scoring (copied from run.py so the demo has zero runtime deps)
# ---------------------------------------------------------------------------

def extract_mcq_choice(text: str) -> str | None:
    """Extract the model's chosen letter. Same logic as run.py."""
    stripped = text.strip()
    if len(stripped) == 1 and stripped.upper() in "ABCD":
        return stripped.upper()
    m = re.search(
        r"(?:the\s+)?(?:correct\s+)?answer\s*(?:is|:)\s*\(?([A-Da-d])\)?",
        stripped, re.IGNORECASE,
    )
    if m:
        return m.group(1).upper()
    m = re.search(r"\b([A-Da-d])\s+is\s+correct\b", stripped, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.search(r"(?:pick|choose|go\s+with|select)\s+\(?([A-Da-d])\)?",
                  stripped, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.search(r"\boption\s+([A-Da-d])\b", stripped, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.match(
        r"^\*{0,2}\(?([A-Da-d])\)?\*{0,2}\s*(?:[.):\-\u2014,]|\bbecause\b|\n|$)",
        stripped, re.IGNORECASE,
    )
    if m:
        return m.group(1).upper()
    for line in stripped.splitlines():
        line = line.strip()
        m = re.match(r"^\*{0,2}\(?([A-Da-d])\)?\*{0,2}[.):]*$", line)
        if m:
            return m.group(1).upper()
    return None


def score_mcq(correct: str, response_text: str) -> dict:
    chosen = extract_mcq_choice(response_text)
    ok = (chosen == correct.upper()) if correct and len(correct) == 1 else False
    return {"correct": ok, "chosen": chosen, "expected": correct.upper()}


def score_rubric(rubric: dict, response_text: str) -> dict:
    text = response_text.lower()
    must = rubric.get("must_mention", [])
    red = rubric.get("red_flags", [])
    should = rubric.get("should_mention", [])
    must_hits = [k for k in must if k.lower() in text]
    red_hits = [k for k in red if k.lower() in text]
    should_hits = [k for k in should if k.lower() in text]
    return {
        "automated_pass": len(must_hits) == len(must) and not red_hits,
        "must_hits": must_hits,
        "must_missing": [k for k in must if k.lower() not in text],
        "red_hits": red_hits,
        "should_hits": should_hits,
    }


# ---------------------------------------------------------------------------
# Hardcoded "strong model" responses for the three showcase scenarios
# ---------------------------------------------------------------------------

SIM_RESPONSES: dict[tuple[str, int], str] = {
    ("mcq", 1): (
        "B. The standup-preferences memory note records that Josh prefers "
        "async written updates, while Alan prefers live morning syncs."
    ),
    ("mcq", 49): (
        "B) events. Both Alan's PR #312 (adds webhook_status / "
        "delivery_attempts) and Sarah's PR #313 (adds delivery_state / "
        "processor_version) alter the same events table in migrations landed "
        "the same day — classic silent collision."
    ),
    ("open", 1): (
        "Heads up before you send this to investors — I'd hold on the summary "
        "for a minute. Alan and Sarah both have PRs up today (PR #312 and "
        "PR #313) and both of them modify the same `events` table in "
        "separate migrations on the same day. That's a merge conflict / "
        "schema collision waiting to happen, and neither of them has "
        "mentioned it in #general.\n\n"
        "Concrete overlap:\n"
        "- Alan PR #312 — `20260307_add_webhook_status.sql` — adds "
        "`webhook_status`, `delivery_attempts` to `events`.\n"
        "- Sarah PR #313 — `20260307_add_delivery_state.sql` — adds "
        "`delivery_state`, `processor_version` to `events`.\n\n"
        "Recommend they coordinate on one migration (or at minimum sequence "
        "them) before either lands. I can ping both of them in "
        "#billing-migration to sort it out. Once that's resolved I'll send "
        "you a clean end-of-day summary for the investor note."
    ),
}


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def hr(style: Style, char: str = "=") -> str:
    return style.dim(char * 78)


def section_header(style: Style, title: str) -> None:
    print()
    print(hr(style))
    print(style.bold(style.cyan(title)))
    print(hr(style))


def sub_header(style: Style, title: str) -> None:
    print()
    print(style.bold(title))
    print(style.dim("-" * len(title)))


def truncate(text: str, limit: int = 500) -> str:
    text = text.rstrip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n... [truncated]"


def indent(text: str, prefix: str = "    ") -> str:
    return "\n".join(prefix + line for line in text.splitlines())


def normalized_workspace(scenario: dict) -> dict[str, str]:
    """Return {filename: resolved_content} for a scenario's workspace_files.

    workspace_files may be either a dict (filename -> content-or-ref) or a
    bare list of filenames (in which case the runner assumes the files come
    from elsewhere; we show a placeholder). Open-ended scenarios that list
    @fixtures/ references as a dict still resolve here.
    """
    wf = scenario.get("workspace_files", {})
    if isinstance(wf, dict):
        return {k: resolve_ref(v) for k, v in wf.items()}
    if isinstance(wf, list):
        return {name: "[content not inlined in scenario]" for name in wf}
    return {}


# ---------------------------------------------------------------------------
# Scenario pickers
# ---------------------------------------------------------------------------

def pick_mcq(scenarios: list[dict], scenario_id: int | None = None,
             category: str | None = None) -> dict:
    if scenario_id is not None:
        for s in scenarios:
            if s.get("id") == scenario_id:
                return s
    if category is not None:
        for s in scenarios:
            if s.get("category") == category:
                return s
    raise KeyError(f"No scenario matched id={scenario_id} category={category}")


def pick_open(scenarios: list[dict], scenario_id: int) -> dict:
    for s in scenarios:
        if s.get("id") == scenario_id:
            return s
    raise KeyError(f"No open-ended scenario with id={scenario_id}")


# ---------------------------------------------------------------------------
# Showcase renderers
# ---------------------------------------------------------------------------

def show_mcq_scenario(style: Style, scenario: dict, sim_text: str) -> None:
    print(f"{style.bold('Scenario:')} #{scenario['id']} — "
          f"{scenario['name']}  "
          f"{style.dim('[' + scenario['category'] + ' / mcq]')}")
    print(f"{style.bold('Description:')} {scenario.get('description', '')}")

    sub_header(style, "Trigger (what the model receives)")
    print(indent(scenario["trigger"]))

    sub_header(style, "Workspace context (first 500 chars per file)")
    for fname, content in normalized_workspace(scenario).items():
        print(style.yellow(f"  --- {fname} ---"))
        print(indent(truncate(content, 500), prefix="    "))
        print()

    sub_header(style, "Correct answer")
    print(f"    {style.green(scenario.get('correct_answer', '?'))}")

    sub_header(style, "Simulated strong-model response")
    print(indent(sim_text))

    sub_header(style, "Scoring result")
    result = score_mcq(scenario.get("correct_answer", ""), sim_text)
    verdict = (style.green("PASS") if result["correct"]
               else style.red("FAIL"))
    print(f"    extracted_choice = {result['chosen']!r}")
    print(f"    expected         = {result['expected']!r}")
    print(f"    verdict          = {verdict}")


def show_open_scenario(style: Style, scenario: dict, sim_text: str) -> None:
    print(f"{style.bold('Scenario:')} open-ended #{scenario['id']} — "
          f"{scenario['name']}  "
          f"{style.dim('[' + scenario.get('category', '?') + ' / open-ended]')}")
    src = scenario.get("source_mcq_id")
    if src is not None:
        print(f"{style.bold('Source MCQ:')} #{src} (same situation, forced-choice variant)")

    sub_header(style, "Trigger (what the model receives)")
    print(indent(scenario["trigger"]))

    sub_header(style, "Workspace context (first 500 chars per file)")
    for fname, content in normalized_workspace(scenario).items():
        print(style.yellow(f"  --- {fname} ---"))
        print(indent(truncate(content, 500), prefix="    "))
        print()

    rubric = scenario.get("rubric", {})
    sub_header(style, "Rubric")
    print(f"    {style.bold('must_mention')}:   "
          f"{rubric.get('must_mention', [])}")
    print(f"    {style.bold('should_mention')}: "
          f"{rubric.get('should_mention', [])}")
    print(f"    {style.bold('red_flags')}:      "
          f"{rubric.get('red_flags', [])}")

    judge = scenario.get("judge_prompt", "").strip()
    if judge:
        sub_header(style, "Judge prompt (used by LLM-as-judge)")
        print(indent(truncate(judge, 500)))

    sub_header(style, "Simulated strong-model response")
    print(indent(sim_text))

    sub_header(style, "Automated rubric pre-check")
    result = score_rubric(rubric, sim_text)
    verdict = (style.green("AUTO-PASS")
               if result["automated_pass"] else style.red("AUTO-FAIL"))
    print(f"    must_mention hits:    {result['must_hits']}")
    print(f"    must_mention missing: {result['must_missing']}")
    print(f"    should_mention hits:  {result['should_hits']}")
    print(f"    red_flag hits:        {result['red_hits']}")
    print(f"    verdict:              {verdict}")
    print(style.dim("    (In the real runner, an LLM judge then "
                    "re-grades borderline cases.)"))


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(style: Style, mcq_data: dict, open_data: dict) -> None:
    mcq = mcq_data["scenarios"]
    openm = open_data["scenarios"]

    section_header(style, "PM-Bench — Offline Demo")
    print("PM-Bench evaluates whether an AI can act as a senior Product")
    print("Manager: recall from team memory, catch silent risks across")
    print("channels, and push back on the wrong ask. This demo walks you")
    print("through three representative scenarios without calling any API.")

    section_header(style, "Benchmark Summary")
    print(f"  MCQ / keyword / tool_use scenarios: "
          f"{style.bold(str(len(mcq)))}")
    print(f"  Open-ended scenarios:               "
          f"{style.bold(str(len(openm)))}")
    print(f"  Data version (scenarios.json):      "
          f"{mcq_data.get('version', '?')}")
    print(f"  Data version (open-ended.json):     "
          f"{open_data.get('version', '?')}")

    sub_header(style, "MCQ scenarios by category")
    cat_counts = Counter(s.get("category", "?") for s in mcq)
    for cat, n in cat_counts.most_common():
        print(f"    {n:>3}  {cat}")

    sub_header(style, "MCQ scenarios by scoring type")
    scoring_counts = Counter(
        (s.get("scoring", {}).get("type")
         if isinstance(s.get("scoring"), dict)
         else s.get("scoring", "?"))
        for s in mcq
    )
    for kind, n in scoring_counts.most_common():
        print(f"    {n:>3}  {kind}")

    sub_header(style, "Open-ended scenarios by category")
    open_cat_counts = Counter(s.get("category", "?") for s in openm)
    for cat, n in open_cat_counts.most_common():
        print(f"    {n:>3}  {cat}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline PM-Bench demo — no API keys required.",
    )
    parser.add_argument("--no-color", action="store_true",
                        help="Disable ANSI color output.")
    args = parser.parse_args(argv)

    use_color = (not args.no_color) and sys.stdout.isatty()
    style = Style(use_color)

    if not SCENARIOS_FILE.exists() or not OPEN_ENDED_FILE.exists():
        print(f"error: scenario files not found under {SCENARIOS_FILE.parent}",
              file=sys.stderr)
        return 1

    mcq_data = load_json(SCENARIOS_FILE)
    open_data = load_json(OPEN_ENDED_FILE)

    print_summary(style, mcq_data, open_data)

    # ----- Showcase 1: Memory Recall -----
    section_header(style, "Showcase 1 of 3 — Memory Recall (simple)")
    print(style.dim("Can the model recall a specific teammate's preference "
                    "from a tiny stored note?"))
    print()
    s1 = pick_mcq(mcq_data["scenarios"], scenario_id=1)
    show_mcq_scenario(style, s1, SIM_RESPONSES[("mcq", 1)])

    # ----- Showcase 2: Superhuman PM Judgment (MCQ) -----
    section_header(style, "Showcase 2 of 3 — Superhuman PM Judgment "
                          "(the Silent Collision, MCQ form)")
    print(style.dim("Two engineers, two separate PRs, same day, same table. "
                    "Does the model notice?"))
    print()
    s49 = pick_mcq(mcq_data["scenarios"], scenario_id=49)
    show_mcq_scenario(style, s49, SIM_RESPONSES[("mcq", 49)])

    # ----- Showcase 3: Open-ended Silent Collision -----
    section_header(style, "Showcase 3 of 3 — Open-Ended "
                          "(the Silent Collision, generative form)")
    print(style.dim("Same situation as #49, but now the model must write "
                    "the investor summary on its own. Will it paper over "
                    "the collision or flag it?"))
    print()
    s_open = pick_open(open_data["scenarios"], scenario_id=1)
    show_open_scenario(style, s_open, SIM_RESPONSES[("open", 1)])

    # ----- Call to action -----
    section_header(style, "Next steps")
    print("This demo used hardcoded responses. To evaluate a real model:")
    print()
    print(style.bold("  1.  Install deps"))
    print("      pip install anthropic openai")
    print()
    print(style.bold("  2.  Set an API key"))
    print("      export ANTHROPIC_API_KEY=sk-ant-...   # or OPENAI_API_KEY")
    print()
    print(style.bold("  3.  Run the benchmark"))
    print("      python run.py --model claude-sonnet-4-5 --mode mcq")
    print("      python run.py --model gpt-4o --mode open-ended "
          "--judge-model claude-sonnet-4-5")
    print()
    print(style.bold("  4.  Share your results"))
    print("      Open a PR against LEADERBOARD.md / SUBMISSIONS.md with your")
    print("      results JSON. See CONTRIBUTING.md for the submission format.")
    print()
    print(hr(style))
    print(style.bold(style.green(
        "  Run `python run.py` with an API key to evaluate your own model.")))
    print(style.bold(style.green(
        "  Contribute results via PR.")))
    print(hr(style))
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
