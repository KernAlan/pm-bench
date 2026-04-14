# PM-Bench

[![CI](https://github.com/KernAlan/pm-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/KernAlan/pm-bench/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-122_passed-green)](tests/)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](VERSION)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Models on leaderboard](https://img.shields.io/badge/leaderboard-6_models-orange)](LEADERBOARD.md)

**A benchmark for AI PM judgment in a noisy engineering workspace.**

PM-Bench tests whether an AI teammate operating in a messy, multi-channel engineering environment can notice the important thing, connect distributed context, react with the right level of intervention, and communicate it in a PM-shaped way.

- **68 MCQ/keyword scenarios** across 10 categories (48 auto-scored, 20 require tool harness)
- **20 open-ended scenarios** with rubric + LLM-judge scoring — tests unprompted judgment
- **5 context-assembly experiments** with explicit kill conditions
- **Item Response Theory analysis** tooling (difficulty, discrimination, contamination)
- **Multi-model answer-key validation** tooling
- **[METHODOLOGY.md](METHODOLOGY.md)** — rigorous methodology documentation
- **[PAPER.md](PAPER.md)** — NeurIPS Datasets & Benchmarks-style paper draft
- **[LEADERBOARD.md](LEADERBOARD.md)** — 6 OpenAI mini/nano models scored, see live results

### Headline result: agentic mode reveals a 31-point capability gap MCQ hides

| Model | MCQ Superhuman 20 (3-8 iter) | **Agentic Superhuman 20 (3 iter)** | Δ |
|---|---|---|---|
| `gpt-5-nano` | 95.00% ±0.00% | **95.00%** ±0.00% | **0** |
| `gpt-5.4-mini` | 100.00% ±0.00% | 91.67% ±3.27% | -8.33 |
| `gpt-5-mini` | 96.88% ±1.79% | 91.67% ±3.27% | -5.21 |
| `gpt-5.4-nano` | 91.25% ±4.69% | 86.67% ±6.53% | -4.58 |
| `gpt-4.1-mini` | 98.00% ±2.40% | **71.67%** ±14.24% | **-26.33** |
| `gpt-4.1-nano` | 88.00% ±3.92% | **56.67%** ±11.78% | **-31.33** |

In **agentic mode**, the workspace files are NOT in the prompt — the model must call `list_files`, `read_file`, and `grep` to investigate. This is what real PM agents do. The MCQ-only mode tests reading comprehension; agentic mode tests the actual capability.

**Reasoning models (GPT-5 family) cluster at 86-95%.** **Non-reasoning models (GPT-4.1 family) collapse 26-31 points** — and become high-variance (±14% CI), suggesting they sometimes investigate well and sometimes don't. GPT-5 nano holds 95% with zero variance across 3 iterations: it always finds the right files.

This validates the construct: PM-Bench in agentic mode tests *active investigation under uncertainty*, not reading comprehension. A user picking a model to deploy as a Slack PM agent based on MCQ scores would have chosen gpt-4.1-mini (98%) over gpt-5-nano (95%); under agentic conditions, that ordering reverses dramatically (gpt-4.1-mini at 71.67% vs gpt-5-nano at 95%).

### Full leaderboard (see [LEADERBOARD.md](LEADERBOARD.md))

**MCQ — Superhuman 20** (3-8 iterations per model):

| Model | Score | 95% CI |
|---|---|---|
| `gpt-5.4-mini` | 100.00% | ±0.00% (n=4) |
| `gpt-4.1-mini` | 98.00% | ±2.40% (n=5) |
| `gpt-5-mini` | 96.88% | ±1.79% (n=8) |
| `gpt-5-nano` | 95.00% | ±0.00% (n=3) |
| `gpt-5.4-nano` | 91.25% | ±4.69% (n=4) |
| `gpt-4.1-nano` | 88.00% | ±3.92% (n=5) |

**MCQ — Full 48** (1-3 iterations):

| Model | Score | 95% CI |
|---|---|---|
| `gpt-5-nano` | 93.75% | n=1 |
| `gpt-5.4-mini` | 91.67% | ±2.36% (n=3) |
| `gpt-5-mini` | 91.67% | n=1 |
| `gpt-4.1-mini` | 90.97% | ±1.36% (n=3) |
| `gpt-4.1-nano` | 81.25% | ±4.08% (n=3) |
| `gpt-5.4-nano` | 80.56% | ±4.91% (n=3) |

**Open-Ended — 20** (rubric + LLM-judge `gpt-4.1-mini`):

| Model | Score | 95% CI |
|---|---|---|
| `gpt-5.4-nano` | 100.00% | n=1 |
| `gpt-5-mini` | 100.00% | n=1 |
| `gpt-5.4-mini` | 98.33% | ±3.27% (n=3) |
| `gpt-4.1-mini` | 95.00% | n=1 |
| `gpt-5-nano` | 95.00% | n=1 |
| `gpt-4.1-nano` | 80.00% | n=1 |

**Headline findings from item analysis:**
- The Superhuman 20 has clearer ranking signal than expected from initial pilot data (12-point spread across mini/nano tier; gpt-4.1-nano at 88% vs gpt-5.4-mini at 100%).
- Two scenarios do most of the discrimination work: **#55 meeting_assassin** (discrimination 0.742) and **#64 roi_translator** (discrimination 0.814).
- **Open-ended is more discriminating than MCQ:** gpt-4.1-nano scores 80% open-ended vs 88% MCQ; the gap suggests the open-ended mode catches PM-judgment failures that MCQ scaffolding hides.
- 1 floor item identified and **fixed** during baseline runs (#30 needed an explicit credentials-status indicator since static context can't simulate runtime credential filtering).
- Anthropic and Google baselines pending — open issue welcomes contributions.

Grounded in realistic simulated team workspaces with real PM failure modes: hidden dependencies, misleading metrics, missing commitments, single-point-of-failure risk, and knowing when to stay quiet.

---

## What PM-Bench tests (and doesn't)

PM-Bench tests **PM-style inference** -- can the model recover the right insight from distributed context when pointed at the right documents? It does not test PM execution -- it won't tell you whether a model can run a sprint planning meeting, write a PRD, or navigate a difficult stakeholder conversation in real time.

The Superhuman PM Judgment scenarios (the core 20) are all multiple-choice. That means the model sees four options and picks one. This is a meaningful test of whether the model can connect dots across documents, but it's a weaker test than "would the model notice this unprompted in a real Slack workspace?" The MCQ format removes the hardest part of the skill (noticing) and isolates the inference part (connecting).

The context-assembly experiments (5 JSONC scenarios) are more ambitious -- they test explicit product hypotheses with kill conditions and produce comparative outputs for human evaluation. These are closer to testing real PM behavior.

**What this means:** A high PM-Bench score indicates strong reading comprehension, cross-document reasoning, and pattern recognition in PM-relevant contexts. It does not prove the model can "do the job of a product manager."

---

## Why PM-Bench?

Most AI benchmarks test knowledge retrieval, coding ability, or reasoning puzzles. None test whether a model can operate as a teammate in an ambiguous, multi-stakeholder environment where the right answer depends on context scattered across channels, documents, and days of conversation.

Product management judgment is a good test domain because:

- **Context is distributed** -- the right call requires synthesizing information from Slack threads, Jira tickets, meeting notes, and tribal knowledge
- **Silence is sometimes the right action** -- knowing when NOT to respond is as important as knowing what to say
- **Tone matters** -- the same information delivered differently to an engineer vs. a VP of Sales produces completely different outcomes
- **Temporal reasoning is essential** -- what happened Tuesday changes the meaning of what someone said Thursday

PM-Bench is inspired by [Terminal-Bench](https://github.com/laude-institute/terminal-bench) (CLI/terminal capabilities) and [EQ-Bench](https://github.com/EQ-bench/EQ-Bench) (emotional intelligence), extending domain-specific evaluation to product management.

---

## The Workspaces

PM-Bench uses two workspace contexts. This is a known coherence gap -- they share thematic DNA but are not one consistent world.

### MCQ scenarios (1-68): Dogfooding context
A 2-person startup (Alan and Josh) building an AI PM agent. Scenarios inject per-scenario workspace files (memory, logs, project state, team info) that vary by scenario -- some introduce a larger cast (Sarah, Marcus, Priya, etc.) for specific stories. The shared identity prompt (`fixtures/identity.md`) defines PM behavior; each scenario supplies its own context.

### Context-assembly experiments (5): Acme Platform Team
A 7-person engineering team at Acme Corp with a billing migration under deadline pressure, a reluctant tech lead absorbing PM duties, a new hire overwhelmed by the codebase, and a VP of Sales who treats timelines as customer promises. The full simulated workspace lives in `workspace/` with 7 days of activity logs.

---

## Categories

| # | Category | Count | Scoring | What It Tests |
|---|----------|-------|---------|---------------|
| 1 | Memory Recall | 8 | mcq | Retrieving specific facts from workspace files |
| 2 | Memory Operations | 3 | tool_use | Saving new information, logging decisions correctly |
| 3 | Judgment & Correction | 3 | tool_use | Knowing when to react, stay quiet, or correct |
| 4 | Synthesis & Robustness | 3 | mcq | Multi-file synthesis, partial info honesty, multi-question |
| 5 | Proactive Outreach | 2 | keyword | Mentioning relevant people, spontaneous notification |
| 6 | Channel Management | 3 | tool_use | Creating channels, inviting people, strategic group DMs |
| 7 | Self-Extending Tools | 6 | tool_use | Loading skills, HTTP requests, scripts, creating capabilities |
| 8 | Credential-Aware Integrations | 6 | tool_use / mcq | OAuth flows, partial connectivity, credential awareness |
| 9 | PM Behavior | 14 | mcq / keyword | Project synthesis, blocker flagging, tone calibration, scope boundaries |
| 10 | Superhuman PM Judgment | 20 | mcq | Cross-channel inference, temporal reasoning, pattern recognition, quantitative analysis |

**Total: 68 scenarios.** Of these, ~36 are MCQ, ~12 are keyword, and ~20 are tool_use. The runner scores MCQ and keyword scenarios automatically (48 scenarios). Tool_use scenarios are always excluded from the runner -- they require a tool-execution harness not included in this repo. Use them as integration tests in your own agent.

---

## Superhuman PM Judgment (20 Scenarios)

The strongest part of PM-Bench. Each scenario provides workspace documents and asks a specific factual question whose answer requires connecting information across files. All are MCQ with plausible distractors drawn from real facts in the workspace.

| # | Story | What It Tests |
|---|-------|---------------|
| 1 | The Silent Collision | Two engineers in different channels both alter the same database table |
| 2 | The Calendar Blindspot | A part-time engineer's schedule vs. a proposed meeting day |
| 3 | The Unasked Question | A sales promise that engineering explicitly scoped out |
| 4 | The Misread Metric | A metric improvement where the definition changed |
| 5 | The Budget Interpreter | Identifying unused infrastructure from cost breakdowns |
| 6 | The Three-Ticket Pattern | Three unrelated support tickets sharing a hidden root cause |
| 7 | The Meeting Assassin | An 8-person meeting where only one question is actually open |
| 8 | The First-Day Briefing | Legacy naming conventions and tribal knowledge for a new hire |
| 9 | The Scope Surgeon | Customer research that contradicts a sales-driven feature request |
| 10 | The Green CI Paradox | 100% green CI with zero edge-case coverage |
| 11 | The Thread Therapist | Two engineers arguing past each other when one already proposed the synthesis |
| 12 | The Silent Failure Pre-mortem | A launch checklist with a specific webhook delivery gap |
| 13 | The Timezone Play | A cross-timezone decision with an unconsulted stakeholder |
| 14 | The Debt Ledger | Aggregating scattered workaround complaints into a quantified cost |
| 15 | The Competitor Signal | A competitor feature that's cheap for us to match |
| 16 | The ROI Translator | Calculating refactor break-even from projected feature velocity |
| 17 | The Reverse Escalation | A VP-escalated "bug" that's actually a spec ambiguity |
| 18 | The Lunch Decision | A casual Slack comment that's actually a major product commitment |
| 19 | The Postmortem Reframe | Identifying what went right in a failed dry-run |
| 20 | The Rate Limit Ghost | Two teams about to collide on a shared API rate limit |

---

## How to Run

### Prerequisites

```bash
pip install anthropic  # or: pip install openai
```

Set your API key:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
# or
export OPENAI_API_KEY=sk-...
```

### Run

```bash
# Run all automatically-scorable scenarios (MCQ + keyword)
python run.py

# Run only the Superhuman PM Judgment scenarios
python run.py --superhuman-only

# Use OpenAI
python run.py --provider openai --model gpt-4o

# Run a specific category
python run.py --category "Memory Recall"

# Run a single scenario by numeric ID
python run.py --scenario 49

# Open-ended mode (20 scenarios, LLM-judge scoring)
python run.py --mode open-ended

# Open-ended with a different-family judge (recommended)
python run.py --mode open-ended --provider anthropic --judge-provider openai

# Dry run -- print prompts without calling the API
python run.py --dry-run
```

### Analysis tools

```bash
# Item Response Theory analysis (after running baselines)
python tools/analyze.py

# Cross-validate authored answers with multiple models as annotators
python tools/validate_answers.py --models claude-sonnet-4-20250514 gpt-4o

# Check for contamination via paraphrased variants
python tools/contamination.py --model claude-sonnet-4-20250514 --n-scenarios 20

# Multi-model baseline orchestration with variance estimation
python tools/multi_run.py --iterations 3 --models claude-sonnet-4-20250514 gpt-4o
```

### Output

The runner prints a scorecard and saves results to `results/`:

```
PM-Bench Results -- claude-sonnet-4-20250514
============================================
Category                                Score      Pct
------------------------------------------------------------
Memory Recall                            5/6     83.3%
Synthesis & Robustness                   3/3    100.0%
Proactive Outreach                       2/2    100.0%
Self-Extending Tools                     1/1    100.0%
Credential-Aware Integrations            3/4     75.0%
PM Behavior                             10/12    83.3%
Superhuman PM Judgment                  16/20    80.0%
------------------------------------------------------------
TOTAL                                   40/48    83.3%
```

(20 tool_use scenarios are always excluded -- they require a tool-execution harness.)

---

## Scoring

### `mcq` -- Multiple Choice
The trigger text includes 4 options (A/B/C/D). The model's response is checked for the correct letter. Primary scoring type for Superhuman PM Judgment.

### `keyword` -- Keyword Presence
The model's response must contain a specific word or phrase (e.g., a person's name, a concept). Used for scenarios where the correct behavior is surfacing a specific piece of context.

### `tool_use` -- Tool Call Inspection (not scored by runner)
Checks whether the model calls the expected tool (e.g., `recall_memory`, `save_memory`, `log_decision`). These 20 scenarios require tool schemas to be sent with the API call, which this runner does not do. They are always excluded from `run.py`. If you're building a PM agent with tools, use these scenarios as integration tests in your own harness.

---

## Repository Structure

```
pm-bench/
├── README.md
├── LICENSE                          # MIT
├── run.py                           # Python evaluation runner
├── fixtures/                        # Shared context for MCQ scenarios
│   ├── identity.md                  # PM identity prompt (dogfooding context)
│   ├── intents.md                   # Strategic context (goals, deadline)
│   ├── rich-project-state.md        # Detailed project state
│   ├── decisions-with-reasoning.md  # Decision log with rationale
│   ├── cross-channel-log.md         # Multi-channel activity log
│   └── stories/                     # 21 story-specific fixtures
│       ├── 01-silent-collision-log.md
│       ├── ...
│       └── 21-rate-limit-context.md
├── scenarios/
│   ├── scenarios.json               # 68 MCQ/keyword/tool-use scenarios
│   └── context-assembly/            # 5 hypothesis-driven experiments (JSONC)
│       ├── 01-intent-impact.jsonc
│       ├── 02-audience-framing.jsonc
│       ├── 03-retrieval-bias.jsonc
│       ├── 04-triage.jsonc
│       └── 05-intent-lifecycle.jsonc
├── workspace/                       # Simulated workspace (context-assembly only)
│   ├── IDENTITY.md                  # Acme Platform Team identity
│   ├── INTENTS.md                   # Active goals and priorities
│   ├── MEMORY.md
│   ├── HEARTBEAT.md
│   ├── logs/                        # 7 days of channel activity
│   └── memory/                      # Knowledge base files
├── tools/                           # Analysis and validation scripts
│   ├── analyze.py                   # Item Response Theory (difficulty/discrimination)
│   ├── validate_answers.py          # Multi-model answer-key cross-validation
│   ├── contamination.py             # Paraphrase-based memorization check
│   └── multi_run.py                 # Multi-model baseline orchestrator
├── submissions/                     # Community submission directory
├── human_baselines/                 # Human baseline submissions
├── METHODOLOGY.md                   # Rigorous methodology + construct validity
├── PAPER.md                         # Academic paper draft (NeurIPS D&B track target)
├── LEADERBOARD.md                   # Model scores (awaiting first submissions)
├── SUBMISSIONS.md                   # How to submit model scores
├── HUMAN_BASELINE.md                # How to contribute human baselines
├── CONTRIBUTING.md                  # Contribution guidelines
└── results/                         # Evaluation output
```

---

## Context Assembly Experiments

Five experiments that test how different prompt construction strategies affect PM-quality output. These are not scored automatically -- they produce comparative outputs for human evaluation. Each includes a **kill condition**: a result that would mean the approach isn't worth pursuing.

| # | Experiment | Hypothesis | Kill Condition |
|---|-----------|-----------|----------------|
| 1 | Intent Impact | INTENTS.md dramatically changes output quality | No meaningful difference between with/without |
| 2 | Audience Framing | Identity + framing produces audience-appropriate writing | Outputs feel like same text at different verbosity |
| 3 | Retrieval Bias | Intent-biased retrieval produces strategically better answers | Unbiased retrieval is equally good |
| 4 | Triage Classification | Cheap model classifies 50 events with >85% accuracy | <85% agreement or >5% missed urgent events |
| 5 | Intent Lifecycle | Model maintains INTENTS.md as 10 events unfold | Updates miss obvious signals or drift from reality |

These validate (or invalidate) architectural decisions in AI agent design, not model capability. They're useful if you're building a PM agent and want to know whether context assembly is worth the token cost.

---

## Background

PM-Bench is derived from [Delegate](https://github.com/J-Reed700/delegate), an AI PM agent that lives in Slack as a teammate. The scenarios are grounded in patterns observed during dogfooding -- situations where the difference between a good PM and a great one is noticing what nobody else noticed.

Created by [Alan Kern](https://github.com/KernAlan) and [Josh Reed](https://github.com/J-Reed700).

---

## Known Limitations

- **MCQ ceiling.** The Superhuman 20 test inference (can you pick the right answer?) not detection (would you notice this unprompted?). A model acing these MCQs may still miss the same patterns in an unstructured environment.
- **Two-world coherence.** The MCQ fixtures and the context-assembly workspace are thematically related but not one consistent universe. See "The Workspaces" above.
- **Keyword scoring is fragile.** A model could give the right answer using different phrasing and fail, or mention the keyword in a wrong answer and pass.
- **No baseline results.** This release doesn't include scores from specific models. Contributions of baseline runs are welcome.
- **Single-domain.** All scenarios are set in a software engineering team. PM judgment in healthcare, hardware, or other domains may require different scenarios.

---

## Contributing

We welcome contributions, especially:

- **Baseline results** from running against specific models
- **New Superhuman scenarios** testing cross-functional reasoning
- **An open-ended evaluation mode** (give the model the workspace and ask "what should the PM flag?" without MCQ scaffolding)
- **A tool-execution harness** for the 20 tool_use scenarios
- **Scoring improvements** for keyword scenarios

---

## License

MIT. See [LICENSE](LICENSE).

## Citation

```bibtex
@misc{pmbench2026,
  title={PM-Bench: A Benchmark for AI Product Management Judgment},
  author={Kern, Alan and Reed, Josh},
  year={2026},
  url={https://github.com/KernAlan/pm-bench}
}
```
