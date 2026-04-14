# PM-Bench Leaderboard

PM-Bench v1.0.0. All scores are from a real PM agent running all 68 scenarios end-to-end. The canonical harness is [Delegate](https://github.com/J-Reed700/delegate). Other harnesses must be equivalently rich (persistent memory, full PM tool surface, multi-turn orchestration) to be accepted - see [SUBMISSIONS.md](SUBMISSIONS.md).

Score = `(PASS + PARTIAL) / 68`, the same rule Delegate's Rust eval harness reports.

Last updated: 2026-04-14.

## Delegate + Model

| Rank | Brain | Provider | Score | Iter | Mean time/scenario | Run date | Raw trace |
|------|-------|----------|-------|------|--------------------|----------|-----------|
| 1 | `gpt-4.1-mini` | openai | 88.24% (60/68) | 1 | 3.3 s | 2026-04-14 | [log](submissions/delegate-agent/delegate_full_eval_history.json) |
| 1 | `gpt-5.4-mini` | openai | 88.24% (60/68) | 1 | 2.6 s | 2026-04-14 | [log](submissions/delegate-agent/delegate_full_eval_history.json) |
| 3 | `gpt-5-nano` | openai | 66.18% (45/68) | 1 | 17.7 s | 2026-04-14 | [log](submissions/delegate-agent/delegate_full_eval_history.json) |

**Pending:** Anthropic (Claude Sonnet / Opus / Haiku), Google (Gemini), additional iterations for variance estimation.

## Human Baselines

Human-PM baselines help contextualize model scores. To contribute, see [HUMAN_BASELINE.md](HUMAN_BASELINE.md).

| Participant Background | Score | N Scenarios | Time per Scenario |
|------------------------|-------|-------------|-------------------|
| (no baselines yet)     | -     | -           | -                 |

## How scoring works

PM-Bench delivers 68 scenarios through a PM-agent harness. Each scenario presents a realistic workspace state (Slack logs, Jira activity, memory files) and a trigger message. The agent responds using its tools. The Rust scorer in Delegate awards:

- **PASS** - agent answered correctly AND used appropriate tools
- **PARTIAL** - answer correct, tool use suboptimal
- **FAIL** - wrong answer or wrong tool usage that caused a wrong outcome

Reported score in this leaderboard is `(PASS + PARTIAL) / total`. Separate PASS-only columns can be added if needed.

## How to submit

1. Run a model as Delegate's brain over all 68 scenarios. Instructions in [SUBMISSIONS.md](SUBMISSIONS.md).
2. Open a PR that:
   - Adds your row to the table above
   - Drops your full `eval_results.json` under `submissions/<handle>/<YYYY-MM-DD>/`
   - Discloses model version, provider, temperature (if applicable), and any Delegate code modifications
3. For 3-iteration runs, include mean + 95% CI.

## Notes on comparability

- Delegate's scoring is deterministic given identical model outputs - but model outputs are not deterministic. Three or more iterations with 95% CI are strongly recommended before citing a rank.
- If you run Delegate with a customized fork (different tool descriptions, different system prompt, different memory layout), disclose that in the submission. Such runs may be listed under a separate "modified-harness" section rather than the canonical leaderboard.
- Human baselines are scored the same way: present the scenario, accept whatever action the human takes (written response, Slack mockup, tool-simulation), then apply the Rust scorer's rubric. Details in `HUMAN_BASELINE.md`.
