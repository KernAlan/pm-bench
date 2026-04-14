# PM-Bench Methodology

## 1. Construct

PM-Bench measures the capability of a model, **when deployed as the brain of a real PM agent**, to perform PM judgment work in a multi-channel software engineering workspace.

Specifically:

- **Cross-channel inference.** Connecting information distributed across Slack channels, Jira comments, meeting notes, and memory files.
- **Temporal reasoning.** Catching that "what happened Tuesday" changes the meaning of "what someone said Thursday."
- **Silent-failure detection.** Identifying problems no individual participant has flagged.
- **Appropriate intervention level.** Knowing when to stay quiet, when to `react` with an emoji, when to `reply` with a paragraph, when to `log_decision`/`save_memory` autonomously.
- **Tool selection under a realistic PM tool surface.** Choosing correctly among tools with overlapping purposes (`reply` vs `log_decision`, `react` vs `recall_memory`, `http_request` vs `load_skill`, etc.).

**What PM-Bench does not measure:** long-horizon product strategy, stakeholder negotiation, customer research synthesis, hiring, cross-organizational political navigation, writing at scale, vision-setting. These are important parts of PM work that this benchmark does not attempt.

## 2. Why a real PM agent is required

A raw LLM is not a PM agent. Without persistent memory, tools for team coordination, credential-aware integrations, and a proactive loop, a model cannot do the work the scenarios ask about. Every scenario assumes an agent architecture with: a tool surface, memory that persists across turns, multi-turn orchestration, and retrieval over workspace state.

Evaluating PM-Bench scenarios against a raw model through static prompting is a different test — of reading comprehension, not PM capability. Stripped-down tool harnesses (e.g. only `list_files`/`read_file`/`grep`) are also insufficient because they do not expose the PM-specific decisions most scenarios hinge on.

The canonical harness is [Delegate](https://github.com/J-Reed700/delegate). Alternative harnesses are accepted only if equivalently rich (persistent memory, full PM tool surface including write-side tools like `save_memory`/`log_decision`/`react`/`reply`, multi-turn orchestration). Submissions from non-qualifying harnesses are rejected.

## 3. Scenario authoring

Scenarios were authored by Alan Kern and Josh Reed based on patterns observed during Delegate's dogfooding. Each scenario is grounded in a real PM failure mode the authors or colleagues encountered.

**Limitation:** 2-author pool, not crowdsourced. GPQA used 61 PhDs; SWE-bench Verified used 93 developers with 3 annotators each. This is a documented threat to validity. Community contribution process is in `CONTRIBUTING.md`.

**Self-audit:** All 20 Superhuman-tier scenarios were audited for answer derivability and distractor quality. One fixture contradiction was found and fixed (#64 `roi_translator`). Eight scenarios had distractors revised to reference workspace entities. See `docs/CONSTRUCT_VALIDITY.md`.

## 4. Scoring

Scoring is delegated to the Delegate Rust eval harness, which classifies each scenario as:

- **PASS** — agent answered correctly AND used appropriate tools
- **PARTIAL** — answer correct, tool use suboptimal
- **FAIL** — wrong answer or wrong tool sequence

Headline score reported on the leaderboard is `(PASS + PARTIAL) / 68`. Separate PASS-only columns can be requested for any submission.

The scoring rubric lives in `apps/delegate/bot/src/eval/scoring.rs` in the Delegate repo. It is deterministic given the agent's output. Model outputs are not deterministic, so multi-iteration runs with 95% CI are strongly recommended.

## 5. Reproducibility

- **Deterministic scenarios.** `scenarios/scenarios.json` is versioned; every scenario has a stable `id`, `name`, and `correct_answer`.
- **Pinned scoring.** Delegate's Rust scorer is committed and versioned. Changes trigger a minor/major PM-Bench bump per [VERSION](VERSION).
- **Shipped workspace.** The full fictional team workspace (`fixtures/`) is committed, not regenerated.
- **Raw traces.** Every submission includes the full `eval_results.json` with per-scenario tool calls and final answer.
- **Recommended protocol.** 3+ iterations per (brain, harness) combo. Report mean + 95% CI. Temperature 0 where applicable.

## 6. Known limitations and threats to validity

- **Selection bias toward Delegate.** Scenarios were authored from Delegate's failure modes. Delegate-like harnesses will score better than equally-capable harnesses built around a different tool surface. Mitigation: invite third-party PM-agent harnesses to submit so the benchmark can be cross-validated.
- **Two-author scenario authoring.** Not crowdsourced. Mitigation: community contribution process.
- **No human PM baseline yet.** Protocol published, no scores submitted.
- **Single domain.** Software engineering teams only. Healthcare, fintech, hardware, consumer PM variants are future work.
- **Single workspace design.** One team, one set of projects. `tools/workspace_variants.py` generates procedurally-substituted variants to reduce memorization risk.
- **Static simulation, not live Slack.** Does not test multi-day state evolution, interruption handling, human-in-loop coordination.
- **Small scenario count by industry standard.** 68 is small vs GPQA Diamond (198) or Terminal-Bench 2.0 (89). Growth to ~150 is a v2 goal.

## 7. Running the benchmark

See `README.md` for authoritative steps. Summary:

1. Clone and set up Delegate, including its Postgres dependency.
2. Configure `DELEGATE_PROVIDER`, `DELEGATE_MODEL`, `DELEGATE_DATABASE_URL`, and the relevant API key.
3. From `delegate/bot/`, run `cargo test --release eval_scorecard -- --ignored --nocapture`.
4. Results land in `eval_results.json`.

## 8. Comparison to related benchmarks

| Benchmark | What it measures | Harness |
|---|---|---|
| [Terminal-Bench](https://github.com/laude-institute/terminal-bench) | Agentic terminal/CLI task completion | Dockerized shell + test scripts |
| [SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/) | Bug fix capability on real GitHub issues | Code repo + pytest |
| [METR RE-Bench](https://metr.org) | Long-horizon AI R&D autonomy | Full research environment |
| [GPQA Diamond](https://arxiv.org/abs/2311.12022) | Graduate-level domain knowledge | Static MCQ |
| [EQ-Bench](https://github.com/EQ-bench/EQ-Bench) | Emotional-intelligence writing | LLM-as-judge |
| **PM-Bench** | **PM agent capability in eng workspaces** | **Delegate or equivalent** |

PM-Bench fills a specific gap: role-specific PM agent evaluation in a collaborative multi-channel environment with memory and proactive behavior. Complementary to Terminal-Bench and SWE-bench, not a replacement.

## 9. Versioning

PM-Bench follows semver. Changes to scenario correct answers, scoring semantics, or the required harness interface trigger a minor or major bump. Current: **v1.0.0** (released 2026-04-14).
