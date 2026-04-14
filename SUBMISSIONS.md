# Submission Guidelines

This document describes how to submit a run to the PM-Bench leaderboard.

## Required fields

Every submission PR must include:

| Field | Description |
|-------|-------------|
| `model` | Exact model version string (e.g. `claude-opus-4-6-20260101`, `gpt-5-2026-03-15`). No aliases. |
| `provider` | anthropic / openai / google / xai / deepseek / local / other |
| `mode` | `mcq-superhuman-20`, `mcq-full-48`, or `open-ended-20` |
| `iterations` | Integer, minimum 3 |
| `temperature` | Float, exact value passed to the API |
| `max_tokens` | Integer, exact value |
| `system_prompt_hash` | SHA-256 of the system prompt used (should match the one in `run.py` — disclose any deviation) |
| `judge_model` | Open-ended only — must differ in family from subject |
| `run_dates` | ISO dates for each iteration |
| `raw_results` | Path to `submissions/<model>/<date>/*.json` in the PR |

## Directory layout for raw results

```
submissions/
  <provider>-<model-slug>/
    YYYY-MM-DD/
      iter_1.json
      iter_2.json
      iter_3.json
      metadata.json   # the fields table above
```

Do not edit `iter_*.json` after the run. They should be byte-identical to what `run.py` emitted.

## Computing the confidence interval

From N iteration scores `x_1 ... x_N`:

```
mean = sum(x) / N
std  = sqrt(sum((x_i - mean)^2) / (N - 1))
ci95 = 1.96 * std / sqrt(N)
```

Report as `mean +/- ci95`. If N < 3, the submission is not eligible for the leaderboard (still acceptable as a data point in discussion).

For per-scenario variance, include a `per_scenario.json` with mean and std per scenario ID.

## Reproducibility checklist

Before opening the PR, confirm:

- [ ] Exact model version string (no "latest" aliases)
- [ ] Temperature and max_tokens disclosed
- [ ] System prompt unchanged from `run.py` (or changes documented)
- [ ] Scenarios unchanged from the pinned commit on `main`
- [ ] Rubric unchanged from `METHODOLOGY.md`
- [ ] Minimum 3 iterations
- [ ] Raw JSON files committed
- [ ] Judge model (if open-ended) is a different family from the subject
- [ ] No retries on individual scenarios — full runs only
- [ ] Commit SHA of the pm-bench repo used, recorded in `metadata.json`

## What counts as a valid submission

**Valid:**
- Running `run.py` as-is against a production API endpoint
- Running against a local/self-hosted model with disclosed quantization and hardware
- Using a fine-tuned variant, provided the fine-tuning data is disclosed at a high level and did not include PM-Bench scenarios

**Invalid (will be rejected):**
- Cherry-picking the best of many runs (submit the full set)
- Modifying scenarios, workspace fixtures, or the rubric
- Retrying individual scenarios that failed
- Using PM-Bench scenarios in training data (contamination)
- Changing the judge prompt without documenting it
- Undisclosed test-time scaffolding beyond what `run.py` provides

If you are uncertain whether a modification is allowed, open an issue before running.

## Disclosure requirements

If the submitter is affiliated with the lab that produces the subject model (employee, contractor, or financially compensated advocate), this MUST be disclosed in the PR description:

> Disclosure: I am [role] at [lab] which produces [model].

Affiliated submissions are welcome and often the highest-quality, but they are flagged in the leaderboard with an asterisk so readers can weight appropriately.

Independent replications of lab submissions are especially valuable and will be annotated.

## Contamination concerns

If your model may have been trained on PM-Bench data (scenarios, workspace, or earlier results), disclose it. We would rather have an honest "possibly contaminated" note than a silently-inflated score.

## Questions

Open an issue with the label `submission-question`.
