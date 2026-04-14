# Contributing to PM-Bench

Thanks for considering a contribution. PM-Bench only works if it reflects real PM work, so contributions from practicing PMs and engineering leads are especially valuable.

## Ways to contribute

### 1. Scenario proposals

A good Superhuman scenario has these properties:

- **Grounded in real PM work**: cross-channel collision, blocker detection, temporal reasoning about stale threads, strategic pushback against a senior stakeholder, quantitative analysis of noisy signals.
- **Requires synthesis, not recall**: the answer should not be lookup-able from a single file. It should require reading multiple workspace artifacts and reconciling them.
- **Has a defensible correct answer**: even if open-ended, a rubric should exist that two experienced PMs would mostly agree on.
- **Time-pressured**: the scenario should be solvable by an experienced human PM in 3-5 minutes, but non-trivial.
- **Not trivially pattern-matchable**: if a junior engineer could answer correctly from the first sentence, it is not Superhuman.

To propose a scenario, open an issue titled `[scenario] <short description>` with:
- The trigger message
- The workspace files it depends on (reference existing fixtures or propose new ones)
- The correct answer + rubric
- Why you believe it is at the Superhuman tier

Scenarios are added via PR only after discussion on the issue.

### 2. Fixture additions

Workspace fixtures live under `fixtures/` and `workspace/`. Good fixtures are:

- **Realistic**: they read like things real teams write
- **Internally consistent**: if JIRA.md says a ticket is blocked, linked Slack fixtures should reflect that
- **Minimal surface**: only include what scenarios need; avoid bloat

### 3. Scoring improvements

If you think the rubric in `METHODOLOGY.md` misses something, or the judge prompt is biased, open an issue with concrete examples. Changes to scoring require:
- A clear statement of the current behavior and the proposed behavior
- At least 3 example scenarios where the change produces a different result
- A re-run of the existing leaderboard entries with the new scoring (contributors can request help with this)

### 4. Human baselines

See [HUMAN_BASELINE.md](HUMAN_BASELINE.md). These are among the most valuable contributions and we actively seek them.

### 5. Paper collaboration

We are interested in co-authoring a short paper on the benchmark and findings. If you have run meaningful experiments, replicated results, or contributed significantly to the scenarios or methodology, reach out via issue titled `[paper] collaboration interest`.

## Code of conduct

- Be professional. Critique the work, not the person.
- Disclose conflicts of interest (lab affiliation, financial stake in a model).
- Respect anonymity requests for human baselines.
- Do not submit scenarios drawn verbatim from any proprietary or NDA-covered source.
- Assume good faith in discussions; escalate by closing threads, not by personalizing them.

## PR checklist

- [ ] The change is scoped (one scenario set, or one fixture cluster, or one doc change - not all three in one PR)
- [ ] If adding a scenario, the rubric/answer is in the PR
- [ ] If changing scoring, existing leaderboard entries are recomputed or a migration plan is stated
- [ ] Doc changes pass a spellcheck
- [ ] No proprietary data included

## Questions

Open an issue. We read all of them.
