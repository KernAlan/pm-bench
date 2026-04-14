# Contributing a Human Baseline

We need human PM baselines to contextualize model scores. If you have PM or engineering-lead experience, consider contributing.

## Protocol

### Setup
- Pick a mode: MCQ or open-ended
- Pick a subset: Superhuman 20 (recommended), or full 48 MCQ, or 20 open-ended
- Time-box: 3-5 minutes per scenario (realistic PM response time)
- No external tools: no Google, no internal docs, only the workspace provided
- Be honest about uncertainty — guessing hurts the baseline

### Procedure
For each scenario:
1. Read `scenarios/scenarios.json` (or `scenarios/open-ended.json`) entry
2. Read the referenced workspace files
3. Answer within the time limit
4. Record your response

### Submission
Fill out the template in `human_baselines/TEMPLATE.md` and submit via PR.

Include:
- Your role/experience (anonymized if preferred: "Staff Eng, 8 yrs PM-adjacent")
- Mode + subset
- Total time
- Per-scenario: response, self-reported confidence (1-5), time spent
- Overall score (self-graded using the benchmark's rubric)

## Why this matters

Benchmarks without human baselines cannot distinguish "hard for everyone" from "solved by the model". GPQA's Diamond tier (Google-proof) is defined by PhDs being unable to answer via Google. ARC-AGI required a 400-person study. We need the same here.

## Grading your own responses

For MCQ: compare your selected letter to the `answer` field in `scenarios/scenarios.json`. Score = correct / total.

For open-ended: use the rubric in `METHODOLOGY.md`. Be strict with yourself. Ideally, have a second human PM grade your responses blind.

## Anonymity

We respect anonymity. You may submit under a pseudonym or a role descriptor ("Senior PM, B2B SaaS, 10 yrs"). We only need enough context to weight the baseline.

## What we are NOT asking for

- Your full work history
- Your employer's name
- Any proprietary information

Just: did a human with relevant background solve this, under time pressure, without tools.
