# Submitting a PM-Bench Score

PM-Bench scores are only accepted from a real PM-agent harness. The canonical harness is [Delegate](https://github.com/J-Reed700/delegate). Alternative harnesses must be equivalently rich (persistent memory, full PM tool surface, multi-turn orchestration) and will be reviewed case-by-case.

## Required

1. **The `eval_results.json` trace.** Delegate writes this automatically after `cargo test eval_scorecard`. It contains every scenario's status, tool-call sequence, and final answer. Submit the file unedited under `submissions/<handle>/<YYYY-MM-DD>/`.
2. **Model + provider version strings.** The exact `DELEGATE_MODEL` and `DELEGATE_PROVIDER` env vars used, pinned to the vendor's published model identifier at the time of the run.
3. **Harness version.** The git SHA of the Delegate commit used. (Delegate's eval persists this automatically.)
4. **Temperature / sampling settings** if non-default, and any other sampling-related configuration.
5. **Affiliation disclosure.** If you work for the vendor whose model you're submitting, say so. Not disqualifying, just needs to be visible.

## Recommended

- **3 or more iterations.** Submit all traces. Report mean + 95% CI.
- **Cost and wall-clock time.** Per-scenario mean, total run time, total token cost where available.
- **Variance analysis.** Standard deviation, per-category breakdown, noted outlier scenarios.

## Accepting PRs

Open a PR that:
- Adds your row to [LEADERBOARD.md](LEADERBOARD.md), preserving rank ordering by score.
- Includes your trace file(s) under `submissions/<handle>/<date>/`.
- Discloses any Delegate code modifications in the PR description. If you ran a fork with modified tool schemas, system prompt, memory layout, or scoring, disclose it — forked-harness submissions are listed in a separate section rather than on the canonical leaderboard.
- References the source repo and commit SHA used.

Maintainers may re-run your submission independently before accepting.

## What is not accepted

- **Static-prompt evaluations** (workspace dumped into the prompt, no tool use). These measure reading comprehension, not PM capability.
- **Stripped-down tool harnesses** (e.g. only `list_files`/`read_file`/`grep`). These do not expose the PM-specific decisions the scenarios test.
- **Modified correct_answers** or fixture content. If you believe a scenario is broken, open an Issue; don't edit the benchmark inline.
- **Ensemble/multi-model submissions** that combine multiple LLMs into one answer. Acceptable only with explicit disclosure and listed separately.

## Example submission

```
submissions/acme-labs-claude-sonnet/2026-05-01/
  eval_results.json         # raw Delegate output
  README.md                 # run notes: temp, cost, notes
  system_info.txt           # (optional) git SHA, Delegate version, Postgres version
```

PR body:
```
Submitting Delegate + claude-sonnet-4-5 results.
3 iterations: 89.7%, 90.1%, 88.8% (mean 89.5%, 95% CI ±0.74%)
Delegate commit: abc1234
Temperature: default
Affiliation: none
```
