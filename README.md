# PM-Bench

[![CI](https://github.com/KernAlan/pm-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/KernAlan/pm-bench/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](VERSION)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**A benchmark for evaluating AI models as the brain of a real PM agent.**

A raw LLM is not a PM agent. Without persistent memory, tools for team coordination, credential-aware integrations, and a proactive loop, a model cannot do the work. PM-Bench is **not** a reading-comprehension test. The only way to score PM-Bench is to run it through a real PM agent.

The canonical harness is [**Delegate**](https://github.com/J-Reed700/delegate): a Rust-based AI PM agent deployed in Slack. Its 15-tool surface drives persistent Postgres-backed memory, OAuth credential management, proactive heartbeat monitoring, and a multi-turn agent loop. Scenarios in this repo were authored from Delegate's real-world failure modes.

PM-Bench consists of two parts: a **dataset of 68 scenarios** (plus 20 open-ended variants, plus 5 context-assembly experiments), and a specification for the **execution harness** (Delegate, or a qualifying equivalent).

---

## 🏆 Leaderboard

All scores from [Delegate](https://github.com/J-Reed700/delegate) running all 68 scenarios end-to-end with the same Rust scorer. Score = `(PASS + PARTIAL) / 68`.

| Rank | Brain | Provider | Score | Iter | Mean time/scenario | Run date | Raw trace |
|------|-------|----------|-------|------|--------------------|----------|-----------|
| 1 | `gpt-4.1-mini` | openai | **88.24%** (60/68) | 1 | 3.3 s | 2026-04-14 | [log](submissions/delegate-agent/delegate_full_eval_history.json) |
| 1 | `gpt-5.4-mini` | openai | **88.24%** (60/68) | 1 | 2.6 s | 2026-04-14 | [log](submissions/delegate-agent/delegate_full_eval_history.json) |
| 3 | `gpt-5-nano` | openai | 66.18% (45/68) | 1 | 17.7 s | 2026-04-14 | [log](submissions/delegate-agent/delegate_full_eval_history.json) |

**Pending:** Anthropic (Claude Sonnet / Opus / Haiku), Google (Gemini), additional iterations for variance estimation. [Submission instructions below.](#how-to-submit-a-score)

### Human baselines

| Participant Background | Score | N Scenarios | Time per Scenario |
|---|---|---|---|
| (no baselines yet) | - | - | - |

[How to contribute a human baseline](#how-to-contribute-a-human-baseline)

### Findings from the current leaderboard

**Reasoning models don't automatically win at multi-tool PM work.** `gpt-5-nano` drops 22 points behind the mini-model tier when given Delegate's 15-tool surface. Inspection of the tool-call traces shows the reasoning models over-think `react`-vs-`reply`-vs-`log_decision` decisions - each intermediate turn burns context on deliberation rather than action. Non-reasoning mini models (`gpt-4.1-mini`, `gpt-5.4-mini`) tie at 88.2% with 5–7× faster wall time.

**Practitioner takeaway.** If you are choosing a brain for a PM agent in production, tool-surface complexity dominates model class. Pick a fast mini model for a rich tool surface; pick a reasoning model only if the tool menu is narrow.

---

## Quickstart

The benchmark is run by Delegate, not a Python CLI in this repo.

```bash
# 1. Clone both repos
git clone https://github.com/KernAlan/pm-bench.git
git clone https://github.com/J-Reed700/delegate.git
cd delegate/bot

# 2. Spin up Postgres (Delegate's memory store)
docker run -d --name delegate-pg -e POSTGRES_PASSWORD=dev \
    -e POSTGRES_DB=delegate -p 5432:5432 postgres:16-alpine

# 3. Configure the brain you want to evaluate
export OPENAI_API_KEY=sk-...
export DELEGATE_PROVIDER=openai
export DELEGATE_MODEL=gpt-4.1-mini
export DELEGATE_DATABASE_URL=postgres://postgres:dev@localhost:5432/delegate

# 4. Run all 68 scenarios. Takes ~3-20 min depending on model speed.
cargo test --release eval_scorecard -- --ignored --nocapture

# 5. Results land in apps/delegate/bot/eval_results.json
```

Per-scenario traces including tool-call sequences are captured in the result JSON.

---

## What's in this repo

```
pm-bench/
├── scenarios/
│   ├── scenarios.json           # 68 scenarios across 10 categories (the benchmark)
│   ├── open-ended.json          # 20 open-ended variants for rubric-based scoring
│   └── context-assembly/        # 5 hypothesis-driven experiments with kill conditions
├── fixtures/
│   ├── identity.md              # shared PM role prompt
│   ├── intents.md               # strategic context (deadline, stakes)
│   ├── rich-project-state.md    # canonical project state
│   └── stories/                 # 21 story-specific fixtures (logs, support tickets, threads, etc.)
├── workspace/                   # full simulated Acme Platform Team workspace (for context-assembly)
├── submissions/
│   └── delegate-agent/          # canonical Delegate eval traces
├── docs/
│   └── CONSTRUCT_VALIDITY.md    # per-scenario self-audit of Superhuman 20
├── tools/
│   ├── validate_schema.py       # scenario schema validation (used in CI)
│   └── workspace_variants.py    # procedural variants for contamination resistance
├── human_baselines/             # human PM baseline submissions (empty so far)
└── README.md, LEADERBOARD.md, METHODOLOGY.md, SUBMISSIONS.md,
    HUMAN_BASELINE.md, CONTRIBUTING.md, CHANGELOG.md, CITATION.cff,
    VERSION, LICENSE
```

---

## The scenarios

68 scenarios across 10 categories. Each is grounded in a real PM failure mode observed during Delegate's dogfooding.

| # | Category | Scenarios | What it tests |
|---|----------|-----------|---------------|
| 1 | Memory Recall | 8 | Retrieving specific facts via `recall_memory` |
| 2 | Memory Operations | 3 | `save_memory`, `log_decision` when new info arrives |
| 3 | Judgment & Correction | 3 | Knowing when to `react` vs `reply` vs stay quiet |
| 4 | Synthesis & Robustness | 3 | Multi-file synthesis, partial-info honesty |
| 5 | Proactive Outreach | 2 | Mentioning the right person on the right thread |
| 6 | Channel Management | 3 | `create_channel`, `invite_to_channel`, `group_dm` |
| 7 | Self-Extending Tools | 6 | `load_skill`, `http_request`, `run_script`, `create_skill` |
| 8 | Credential-Aware Integrations | 6 | OAuth flows, partial connectivity, credential status |
| 9 | PM Behavior | 14 | Project synthesis, blocker flagging, tone calibration, scope boundaries |
| 10 | **Superhuman PM Judgment** | **20** | **Cross-channel inference, temporal reasoning, pattern recognition, strategic pushback, quantitative analysis** |

### The Superhuman 20

These are the headline scenarios - each tests a specific real PM failure mode:

| # | Story | What it tests |
|---|-------|---------------|
| 49 | Silent Collision | Two engineers in different channels both alter the same database table |
| 50 | Calendar Blindspot | A part-time engineer's schedule vs a proposed meeting day |
| 51 | Unasked Question | A sales promise that engineering explicitly scoped out |
| 52 | Misread Metric | A metric improvement where the definition changed |
| 53 | Budget Interpreter | Identifying unused infrastructure from cost breakdowns |
| 54 | Three-Ticket Pattern | Three unrelated support tickets sharing a hidden root cause |
| 55 | Meeting Assassin | An 8-person meeting where only one question is actually open |
| 56 | First-Day Briefing | Legacy naming conventions and tribal knowledge for a new hire |
| 57 | Scope Surgeon | Customer research that contradicts a sales-driven feature request |
| 58 | Green CI Paradox | 100% green CI with zero edge-case coverage |
| 59 | Thread Therapist | Two engineers arguing past each other when one already proposed synthesis |
| 60 | Silent Failure Pre-mortem | A launch checklist with a specific webhook delivery gap |
| 61 | Timezone Play | A cross-timezone decision with an unconsulted stakeholder |
| 62 | Debt Ledger | Aggregating scattered workaround complaints into a quantified cost |
| 63 | Competitor Signal | A competitor feature that's cheap for us to match |
| 64 | ROI Translator | Calculating refactor break-even from projected feature velocity |
| 65 | Reverse Escalation | A VP-escalated "bug" that's actually a spec ambiguity |
| 66 | Lunch Decision | A casual Slack comment that's actually a major product commitment |
| 67 | Postmortem Reframe | Identifying what went right in a failed dry-run |
| 68 | Rate Limit Ghost | Two teams about to collide on a shared API rate limit |

Per-scenario audit notes and distractor quality analysis are in [docs/CONSTRUCT_VALIDITY.md](docs/CONSTRUCT_VALIDITY.md).

---

## How scoring works

PM-Bench delivers 68 scenarios through the PM-agent harness (Delegate). Each scenario presents a realistic workspace state - Slack logs, Jira activity, memory files - and a trigger message. The agent responds using its tools. Delegate's Rust scorer classifies each scenario as:

- **PASS** - agent answered correctly AND used appropriate tools
- **PARTIAL** - answer correct, tool use suboptimal
- **FAIL** - wrong answer or wrong tool sequence that caused a wrong outcome

Headline score reported here is `(PASS + PARTIAL) / 68`. Separate PASS-only columns are accepted on request. The scoring rubric is deterministic given the agent's output - it's encoded in `apps/delegate/bot/src/eval/scoring.rs` in the Delegate repo.

Model outputs are not deterministic, so 3 or more iterations with 95% CI are strongly recommended before citing a rank.

---

## How to submit a score

1. **Run Delegate against all 68 scenarios.** Follow the [Quickstart](#quickstart). For publication-quality numbers, do 3 or more iterations.
2. **Keep the raw `eval_results.json`.** Delegate writes this automatically with per-scenario tool-call sequences, answer text, and PASS/PARTIAL/FAIL classification.
3. **Open a PR** that:
   - Adds your row to the leaderboard table in this README (preserving rank ordering by score)
   - Drops the trace(s) under `submissions/<handle>/<YYYY-MM-DD>/`
   - Discloses: exact model version, provider, temperature, Delegate commit SHA used, and any code modifications to Delegate (forks go on a separate table, not the canonical leaderboard)
   - Discloses affiliation if you work for the vendor

**Not accepted:**

- Static-prompt evaluations (workspace dumped into the prompt, no tool use)
- Stripped-down tool harnesses (e.g. only `list_files`/`read_file`/`grep`) - these don't expose the PM-specific decisions
- Modified scenarios or correct answers - open an Issue if you believe a scenario is broken
- Ensemble/multi-model submissions without explicit disclosure

Full submission guide: [SUBMISSIONS.md](SUBMISSIONS.md).

---

## How to contribute a human baseline

Human-PM baselines contextualize model scores. We want senior PMs, tech leads, and experienced engineering managers to sit down with the Superhuman 20 and tell us how they do.

Protocol summary:

- Pick a subset (Superhuman 20 recommended)
- Time-box to ~5 minutes per scenario
- No external tools, no Google, just the workspace provided
- Record your response and self-reported confidence
- Open a PR against `human_baselines/` with the filled template

Full protocol: [HUMAN_BASELINE.md](HUMAN_BASELINE.md). Template: [human_baselines/TEMPLATE.md](human_baselines/TEMPLATE.md).

---

## Context-assembly experiments

In addition to the 68 scored scenarios, PM-Bench includes 5 hypothesis-driven experiments that test how different prompt-construction strategies affect PM-quality output. Each includes an explicit **kill condition** - a result that would mean the approach isn't worth pursuing.

| # | Experiment | Hypothesis | Kill Condition |
|---|-----------|-----------|----------------|
| 1 | Intent Impact | `INTENTS.md` dramatically changes output quality | No meaningful difference between with/without |
| 2 | Audience Framing | Identity + framing produces audience-appropriate writing | Outputs feel like same text at different verbosity |
| 3 | Retrieval Bias | Intent-biased retrieval produces strategically better answers | Unbiased retrieval is equally good |
| 4 | Triage Classification | Cheap model classifies 50 events with >85% accuracy | <85% agreement or >5% missed urgent events |
| 5 | Intent Lifecycle | Model maintains `INTENTS.md` as 10 events unfold | Updates miss obvious signals or drift from reality |

These validate (or invalidate) architectural decisions in AI agent design, not model capability. They're useful if you're building a PM agent and want to know whether context assembly is worth the token cost.

---

## Known limitations

- **Selection bias toward Delegate.** Scenarios were authored from Delegate's own failure modes. Delegate-like harnesses will score better than equally-capable harnesses built around a different tool surface. Third-party qualifying harnesses are welcome so the benchmark can be cross-validated.
- **Scenarios were authored by 2 people** (Alan Kern, Josh Reed). Not crowdsourced. GPQA used 61 PhDs; SWE-bench Verified used 93 developers. A community contribution process is open via [CONTRIBUTING.md](CONTRIBUTING.md).
- **No human PM baseline submissions yet.** Protocol is published; no data.
- **Single domain** (software engineering teams). Healthcare / hardware / consumer / enterprise PM variants are future work.
- **Simulated workspace, not live Slack.** Does not test multi-day state evolution, interruption handling, or real stakeholder reaction.
- **Small scenario count by industry standard.** 68 vs GPQA Diamond (198) or Terminal-Bench 2.0 (89). Growth to ~150 is a v2 goal.
- **One floor-effect scenario** (#30) was identified and fixed during baseline runs. Self-audit of all Superhuman 20 is in [docs/CONSTRUCT_VALIDITY.md](docs/CONSTRUCT_VALIDITY.md).

---

## Contributing

Welcome contributions:

- **New scenarios**, especially for cross-functional PM failure modes not yet covered
- **New qualifying harnesses** so the benchmark can be cross-validated beyond Delegate
- **Baseline runs** against other model families (Anthropic, Google, open-source)
- **Human-PM baseline submissions**
- **Scenario translation** into other domains (healthcare PM, fintech PM, etc.)

Full guide: [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Citation

```bibtex
@misc{pmbench2026,
  title={PM-Bench: A Benchmark for AI Product Management Judgment in Multi-Stakeholder Software Environments},
  author={Kern, Alan and Reed, Josh},
  year={2026},
  url={https://github.com/KernAlan/pm-bench}
}
```

Or use the machine-readable [CITATION.cff](CITATION.cff).

---

## Background

PM-Bench and [Delegate](https://github.com/J-Reed700/delegate) are authored by [Alan Kern](https://github.com/KernAlan) and [Josh Reed](https://github.com/J-Reed700). PM-Bench is MIT-licensed.

Further reading:

- [METHODOLOGY.md](METHODOLOGY.md) - construct, scoring, threats to validity, comparison to related benchmarks
- [LEADERBOARD.md](LEADERBOARD.md) - full leaderboard (mirror of the table above)
- [SUBMISSIONS.md](SUBMISSIONS.md) - detailed submission requirements
- [HUMAN_BASELINE.md](HUMAN_BASELINE.md) - human baseline protocol
- [CONTRIBUTING.md](CONTRIBUTING.md) - contribution guide
- [CHANGELOG.md](CHANGELOG.md) - version history
- [docs/CONSTRUCT_VALIDITY.md](docs/CONSTRUCT_VALIDITY.md) - per-scenario self-audit
