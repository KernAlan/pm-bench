# PM-Bench Leaderboard

Last updated: 2026-04-13

## How scores are computed

Each reported score is:
- The mean of N iterations (minimum 3 recommended)
- 95% confidence interval: plus/minus 1.96 x (std / sqrt(N))
- Judge model must be different from subject model for open-ended scores
- Temperature and iteration count must be disclosed with the submission
- Raw `results/*.json` files must be attached under `submissions/<model>/<date>/`

Submissions that cherry-pick runs, alter scenarios, or change the rubric are rejected.

## MCQ Mode — Superhuman 20

The 20 scenarios flagged as requiring superhuman PM reasoning (cross-channel collision detection, temporal reasoning, strategic pushback, quantitative analysis).

| Rank | Model | Score | 95% CI | Iterations | Date | Submitter |
|------|-------|-------|--------|------------|------|-----------|
| — | (awaiting first submission) | — | — | — | — | — |

## MCQ Mode — Full 48 (all non-tool-use scenarios)

| Rank | Model | Score | 95% CI | Iterations | Date | Submitter |
|------|-------|-------|--------|------------|------|-----------|
| — | (awaiting first submission) | — | — | — | — | — |

## Open-Ended Mode — 20 scenarios

Scored by an LLM judge using the rubric in `METHODOLOGY.md`. The judge model must be a different model family from the subject.

| Rank | Subject Model | Judge Model | Score | 95% CI | Iterations | Date | Submitter |
|------|--------------|-------------|-------|--------|------------|------|-----------|
| — | (awaiting first submission) | — | — | — | — | — | — |

## Human Baselines

Human-PM baselines help contextualize model scores. A benchmark without them cannot distinguish "hard for everyone" from "solved by the model". **Contributions welcome** — see [HUMAN_BASELINE.md](HUMAN_BASELINE.md).

| Participant Background | Mode | Score | N Scenarios | Time per Scenario |
|------------------------|------|-------|-------------|-------------------|
| (no baselines yet) | — | — | — | — |

## How to submit

1. Run `python run.py` or `python run.py --mode open-ended` for at least 3 iterations.
2. Fill in the submission template (see [SUBMISSIONS.md](SUBMISSIONS.md)).
3. Open a PR adding your row to the appropriate table and attaching your `results/*.json` files under `submissions/<model>/<date>/`.

Rows are ordered by mean score, ties broken by tighter CI.
