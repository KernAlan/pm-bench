# PM-Bench

[![CI](https://github.com/KernAlan/pm-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/KernAlan/pm-bench/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](VERSION)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**A benchmark for evaluating AI models as the brain of a real PM agent.**

A raw LLM is not a PM agent. Without persistent memory, tools for team coordination, credential-aware integrations, and a proactive loop, a model cannot do the work. PM-Bench is not a reading-comprehension test. **The only way to score PM-Bench is to run it through a real PM agent.**

The canonical harness is [**Delegate**](https://github.com/J-Reed700/delegate): a Rust-based AI PM agent deployed in Slack. Its 15-tool surface (`recall_memory`, `save_memory`, `log_decision`, `reply`, `react`, `channel_history`, `connect_integration`, `jira_search`, `gcal_list_events`, `load_skill`, `create_skill`, `http_request`, `run_script`, `invite_to_channel`, `create_channel`, `group_dm`) drives persistent Postgres-backed memory, OAuth credential management, proactive heartbeat monitoring, and a multi-turn agent loop. Scenarios in this repo were authored from Delegate's real-world failure modes.

If you want to submit results, run a model as Delegate's brain and submit the full `eval_results.json`. Submissions from other harnesses are only accepted if that harness is equivalently rich (persistent memory, full PM tool surface, multi-turn orchestration). Static-prompt runs and stripped-down tool harnesses do not produce comparable scores and are not accepted.

---

## 🏆 Leaderboard

Delegate + model, PM-Bench v1.0, all 68 scenarios.

| Brain (OpenAI) | Score | Iterations | Mean time/scenario | Raw trace |
|---|---|---|---|---|
| `gpt-4.1-mini` | **60 / 68 = 88.2%** | 1 | 3.3 s | [trace](submissions/delegate-agent/delegate_full_eval_history.json) |
| `gpt-5.4-mini` | **60 / 68 = 88.2%** | 1 | 2.6 s | [trace](submissions/delegate-agent/delegate_full_eval_history.json) |
| `gpt-5-nano` | 45 / 68 = 66.2% | 1 | 17.7 s | [trace](submissions/delegate-agent/delegate_full_eval_history.json) |

Anthropic and Google baselines pending. See [SUBMISSIONS.md](SUBMISSIONS.md) for how to add a row.

### Findings

**Reasoning models don't automatically win at multi-tool PM work.** `gpt-5-nano` drops 22 points behind the mini-model tier when given Delegate's 15-tool surface. Inspection of the tool-call traces shows the reasoning models over-think `react`-vs-`reply`-vs-`log_decision` decisions — each intermediate turn burns context on deliberation rather than action. Non-reasoning mini models (4.1-mini, 5.4-mini) tie at 88.2% with 5–7× faster wall time.

**Practitioner takeaway.** If you are choosing a brain for a PM agent in production, tool-surface complexity dominates model class. Pick a fast mini model for a rich tool surface; pick a reasoning model only if the tool menu is narrow.

---

## What's in this repo

```
pm-bench/
├── scenarios/
│   ├── scenarios.json           # 68 scenarios across 10 categories (the benchmark)
│   ├── open-ended.json          # 20 open-ended variants (optional for Delegate-like harnesses)
│   └── context-assembly/        # 5 hypothesis-driven experiments
├── fixtures/                    # workspace context documents
├── submissions/
│   ├── delegate-agent/          # canonical Delegate eval traces
│   └── openai-baselines/        # archival / reproducibility data
├── METHODOLOGY.md               # rigorous methodology
├── PAPER.md                     # paper draft
├── LEADERBOARD.md               # Delegate + model scores
├── HUMAN_BASELINE.md            # how to contribute a human PM baseline
├── SUBMISSIONS.md               # how to submit a model score
└── CONTRIBUTING.md
```

## How to run PM-Bench

1. Clone and set up [Delegate](https://github.com/J-Reed700/delegate). Spin up its Postgres dependency and configure the provider + model you want to evaluate.
2. From `delegate/bot/`, run `cargo test --release eval_scorecard -- --ignored --nocapture`. This runs all 68 scenarios against Delegate's real agent loop.
3. Results land in `eval_results.json`.
4. Submit by opening a PR that adds your row to [LEADERBOARD.md](LEADERBOARD.md) and drops the `eval_results.json` under `submissions/<your-handle>/<date>/`.

## Scenarios

The 68 scenarios span 10 categories of PM work. Each was designed from a real pattern observed during Delegate's dogfooding — situations where a PM failing to notice something caused real cost.

| Category | Count | Tests |
|---|---|---|
| Memory Recall | 8 | Retrieving specific facts via `recall_memory` |
| Memory Operations | 3 | `save_memory`, `log_decision` when new info arrives |
| Judgment & Correction | 3 | Knowing when to `react` vs `reply` vs stay quiet |
| Synthesis & Robustness | 3 | Multi-file synthesis, partial-info honesty |
| Proactive Outreach | 2 | Mentioning the right person on the right thread |
| Channel Management | 3 | `create_channel`, `invite_to_channel`, `group_dm` |
| Self-Extending Tools | 6 | `load_skill`, `http_request`, `run_script`, `create_skill` |
| Credential-Aware Integrations | 6 | OAuth flows, partial connectivity, credential status |
| PM Behavior | 14 | Project synthesis, blocker flagging, tone calibration, scope boundaries |
| Superhuman PM Judgment | 20 | Cross-channel inference, temporal reasoning, pattern recognition |

The **Superhuman 20** is the headline subset — each scenario is a real PM failure mode (silent collision across channels, misleading metric with changed definition, unasked commitment in a parallel thread, etc.). See [docs/CONSTRUCT_VALIDITY.md](docs/CONSTRUCT_VALIDITY.md) for per-scenario audit notes.

## Known limitations

- **Scenarios were authored by 2 people** (Alan Kern, Josh Reed). Not crowdsourced. Documented in [METHODOLOGY.md](METHODOLOGY.md).
- **Benchmark was built from Delegate's failure modes.** This is selection bias working in Delegate's favor — unavoidable for now. We'd like third-party PM-agent harnesses to submit scores so the benchmark can be cross-validated.
- **No human PM baseline yet.** Protocol in [HUMAN_BASELINE.md](HUMAN_BASELINE.md).
- **Single domain** (software engineering teams). Healthcare / hardware / consumer / enterprise PM variants are future work.
- **Simulated workspace, not live Slack.** Does not test multi-day state evolution, interruption handling, or human-in-loop coordination.

## Background

PM-Bench and Delegate are authored by [Alan Kern](https://github.com/KernAlan) and [Josh Reed](https://github.com/J-Reed700). PM-Bench is MIT-licensed. Delegate's source is at its own repo.

## Citation

```bibtex
@misc{pmbench2026,
  title={PM-Bench: A Benchmark for AI Product Management Judgment in Multi-Stakeholder Software Environments},
  author={Kern, Alan and Reed, Josh},
  year={2026},
  url={https://github.com/KernAlan/pm-bench}
}
```
