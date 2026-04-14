# PM-Bench Methodology

**Version:** 1.0
**Last updated:** 2026-04-13

This document describes what PM-Bench measures, how scenarios are constructed and scored, and the known threats to validity. It is intended for ML researchers, engineering leaders evaluating AI agents, and practitioners building AI teammates. We have modeled the structure loosely on the methodology sections of GPQA, SWE-bench Verified, PRBench, BigCodeBench, and MedXpertZQA.

PM-Bench is new, authored data. We are explicit about what has been validated, what has not, and where the scoring is fragile. Read the limitations section (§5) before citing any score.

---

## 1. Construct

PM-Bench measures **PM-style inference and judgment in a noisy engineering workspace**. Concretely, we evaluate whether a model can:

1. **Connect distributed context.** Relevant facts are spread across multiple channels, threads, decision logs, and retrospectives. A correct answer often requires joining two or three separate pieces of evidence that no single document states outright.
2. **Detect subtle problems.** Cross-channel collisions, stale threads, silent blockers, decisions that contradict earlier intents, and divergences between stated priorities and actual team behavior. These are the signals a competent human PM notices and an under-grounded model does not.
3. **Respond with appropriate intervention level.** Some situations require a direct answer, some require a question, some require escalation to a human owner, and some require doing nothing. Picking the right *level of intervention* is part of the PM role and PM-Bench scenarios grade for it.

These three capacities together — what we call *PM judgment* — are the construct. When a scenario is designed, at least one of these three capacities should be the thing being stressed; scenarios that test pure factual recall without requiring joining, detection, or calibrated response are labeled as Memory Recall and are kept separate from the judgment categories.

### What PM-Bench Does NOT Measure

PM-Bench is deliberately a *judgment* benchmark, not a *capability* benchmark. It does not measure:

- **Execution.** PM-Bench does not test whether a model can write a spec document, file a correctly-formatted Jira ticket, or draft a stakeholder update. Those are valuable but they are not what this benchmark scores.
- **Long-horizon planning.** Every scenario is a single-turn decision given a fixed workspace snapshot. We do not evaluate multi-week roadmap construction, sequencing of epics, or planning under evolving constraints.
- **Real-time stakeholder management.** There is no simulated human on the other end, no negotiation, no escalation tree to walk. The model sees a workspace and a trigger; it produces one response.
- **Tool use in live systems.** The `tool_use` scenarios that exist in `scenarios.json` are deliberately excluded from the default runner — they require an agent harness with real tool schemas and are meant as integration tests for teams building agents, not as benchmark items.
- **Long-context retrieval at scale.** Workspaces are curated to fit in a typical model context window. We are not testing whether a model can find a needle in 500K tokens of Slack.

A model that scores well on PM-Bench is not necessarily a good PM agent. It is a model whose *judgment layer*, under idealized retrieval, is aligned with how a thoughtful human PM would read the same workspace.

---

## 2. Scenario Categories

PM-Bench v1.0 contains **68 MCQ/keyword scenarios**, **5 context-assembly experiments**, and (currently being added) **20 open-ended scenarios**. Scenarios are grouped into categories that stress different aspects of the construct.

### Memory Recall
Tests whether the model can locate and report facts that are literally stated in the workspace. This is the retrieval floor — a model that fails here has no hope on the harder categories, so these serve as sanity checks and as a way to separate retrieval failure from judgment failure. Example question shape: "Which engineer is on-call for the payments service this week?"

### PM Behavior
Tests role-appropriate response. Given a realistic trigger (a question in a channel, a surfaced contradiction, a reported blocker), does the model respond the way a competent PM would? This category catches models that have the right facts but produce the wrong *kind* of response — answering with a one-liner when escalation is called for, or escalating a routine question, or volunteering a decision that is not the PM's to make.

### Superhuman PM Judgment
The core category (20 scenarios). Designed to be difficult for a distracted human PM and answerable by a careful reader of the full workspace. Subcategories include:
- **Cross-channel collision detection** — two teams doing overlapping or conflicting work in separate channels.
- **Temporal reasoning** — decisions that were sound when made but are now stale; commitments whose window has closed.
- **Pattern recognition** — recurring incident shapes, a sprint that rhymes with a previous failed sprint, a hiring pattern.
- **Strategic pushback** — cases where the correct answer is "this is the wrong question" or "the stated priority contradicts the actual intent document."
- **Quantitative analysis** — reading metrics, computing a small number, noticing a ratio is off.

This category is the answer to the question "what would a *good* PM catch that a mediocre one would miss?"

### Context Assembly
5 experiments that probe whether the model correctly assembles relevant context before answering. Rather than scoring a final answer, these score the model's retrieval and joining behavior when multiple documents must be combined. These are closer to probes than benchmark items and are reported separately.

### Open-Ended (v1.0, in progress)
20 scenarios with no single correct letter. Instead, each scenario has a rubric (`must_mention`, `should_mention`, `red_flags`) and is scored by an LLM judge. This category exists because MCQ has a ceiling effect (see §5) — a model can recognize the right answer among four options without being able to *produce* it unprompted. Open-ended mode tests generation, not just discrimination.

---

## 3. Data Collection and Authoring

**PM-Bench is authored, not crowd-sourced.** Every scenario was written by Alan Kern or Josh Reed, the authors of this benchmark, during and after the development of Delegate — an AI PM agent that lives in Slack as a teammate, which the authors have been dogfooding on their own team.

Each scenario is grounded in a real PM failure mode. Specifically:

- A subset of Superhuman PM Judgment scenarios are drawn directly from situations where Delegate's earlier triage, retrieval, or reasoning layers failed in a way the authors could point to.
- A subset are drawn from situations where a human PM on a team the authors have worked with missed a cross-channel collision, a stale commitment, or a pattern.
- A subset are constructed adversarially — the authors asked "what is the smallest workspace that would cause a competent reader to miss X?" and wrote a scenario that instantiates it.

We want to be explicit that this is both a limitation and a strength.

**Limitation.** Two authors is a small pool. Our collective blind spots are encoded into the benchmark. Some scenarios may reflect idiosyncratic views of what "good PM judgment" looks like rather than a broadly shared consensus. Our taste for what is "too obvious" vs. "too cute" is not calibrated against anyone else's.

**Strength.** Because the pool is small and the authors are in close contact, design philosophy is coherent across the benchmark. Scenarios do not drift in difficulty, framing, or what counts as a good answer in the way that crowd-sourced benchmarks often do. Every scenario can be traced back to a real failure mode or a principled adversarial construction, not a task-worker's guess at what PM judgment might look like.

We plan to open the benchmark to community-contributed scenarios with explicit provenance tags (`authored-by`, `grounded-in`, `adversarial-construction`) so that the mix can be audited.

---

## 4. Scoring Methodology

PM-Bench uses three scoring types. The scoring algorithm is committed in `run.py` and versioned with the benchmark — future algorithmic changes will bump the benchmark version (see §10).

### 4.1 MCQ Scoring

MCQ scenarios present four options (A/B/C/D) and have exactly one correct letter in `correct_answer`. The `extract_mcq_choice` function in `run.py` is designed to avoid two failure modes: (1) extracting a letter from a phrase like "Not B — the answer is C" and returning B, and (2) failing to extract at all when the model formats its answer in a non-standard way.

The extractor checks the following patterns **in priority order**; the first match wins:

1. **Exact match.** The entire stripped response is a single letter A/B/C/D (case-insensitive).
2. **Explicit answer phrases.** `"the answer is X"`, `"correct answer is X"`, `"answer: X"`, or `"X is correct"`. These are the highest-confidence signals of a chosen answer and are checked before any positional pattern.
3. **Selection verbs.** `"pick X"`, `"choose X"`, `"go with X"`, `"select X"`, or `"option X"`. Also high-confidence; the verb disambiguates "pick C" from "C is tempting."
4. **Leading letter plus delimiter.** The response *starts* with a letter followed by a delimiter: `.`, `)`, `:`, `-`, em-dash, comma, the word `because`, a newline, or end-of-string. Asterisks and parentheses around the letter (bold or "(C)") are tolerated. This catches responses of the form `"B. The CSM should..."` but deliberately does not match `"B is tempting"` because `is` is not in the delimiter set.
5. **Letter on its own line.** A line consisting of just a letter, optionally with enclosing parens/asterisks and trailing punctuation. Catches models that output the letter on line 1 and explanation below.

If none of these patterns match, `extract_mcq_choice` returns `None` and the scenario is marked incorrect. We prefer a confident null over a guess.

**Self-test.** The extractor ships with a 17-case self-test covering: plain letter, bolded `**B**`, parenthesized `(C)`, "the answer is C", "Not B — C is correct", "B is tempting, but C", "I would pick C", "Option A because...", letter on own line, explanation-only responses with no letter, and a handful of adversarial cases drawn from actual model outputs during development. All 17 cases pass; see `run.py` test block.

**Known failure modes.** Models that hedge across multiple letters ("either B or C, depending on...") will typically be picked up as the first matched letter, which may or may not reflect their intent. Models that give no letter at all are marked incorrect even if their prose answer is correct — this is by design, because the benchmark is testing whether the model commits to a choice.

### 4.2 Keyword Scoring

Keyword scenarios check whether a required string (`correct_answer`) appears as a case-insensitive substring in the response. This is the simplest possible scoring rule and it is **fragile**.

Specifically:
- **Paraphrase failure.** A correct response that uses a synonym or restructures the sentence will be scored wrong. If the keyword is `"payments service"` and the model says `"the payments team's service"`, a human would mark it correct and the scorer will not.
- **False positives.** A wrong answer that happens to contain the keyword will be scored correct. If the keyword is `"on-call"` and the model's answer is a long paragraph that happens to contain that phrase while missing the actual point, the scorer will pass it.
- **No partial credit.** Keyword scoring is binary.

We use keyword scoring only where the expected answer is genuinely a short, specific string that a correct response cannot avoid producing (names of people, service names, specific numeric values in context). Even so, it is the weakest link in the scoring pipeline.

**Recommended upgrade path.** Keyword scoring should be replaced in v2.0 with either embedding-based similarity (with a published threshold and a published embedding model) or LLM-judge scoring with the same protocol as the open-ended category. We are not making that change in v1.0 because we want the scoring of existing results to remain stable while the benchmark is being established; but consumers should weight keyword-scored categories accordingly.

### 4.3 LLM-as-Judge Scoring (Open-Ended)

The 20 open-ended scenarios have no correct letter. They are graded by a rubric and an LLM judge. Each scenario carries:

- `must_mention`: a list of facts, entities, or considerations that the response must include. Missing any one of these is an automatic fail regardless of how good the rest of the response is.
- `should_mention`: a list of items that a strong response covers. The judge scores coverage as a fraction.
- `red_flags`: response patterns that disqualify a response even if coverage is high. Examples: committing to a decision that is not the PM's to make, fabricating facts not present in the workspace, escalating when the correct move is to answer in-channel.

**Judge prompt protocol.** The judge receives: the scenario's workspace, the trigger, the model's response, and the rubric. The judge outputs, in JSON: the list of `must_mention` items present, the fraction of `should_mention` items present, the list of `red_flags` triggered, and a final integer score in `[0, 5]` with a short justification. The final 0/1 correctness for benchmark purposes is `score >= 4 AND no red flags AND all must_mention items present`.

**Judge model selection.** We strongly recommend using a **different model family** as judge than the model being evaluated, to reduce self-preference bias. For example, evaluate Claude models with a GPT-family judge and vice versa. Reported scores should always state which judge was used.

**Judge run stability.** LLM judges are stochastic. We recommend running the judge **3–5 times per response** and either majority-voting the binary outcomes or averaging the 0–5 scores and thresholding. Single-run judge scores should not be cited as the benchmark number for a model.

**What this does not fix.** LLM-judge scoring inherits the biases of the judge model. If the judge shares a blind spot with the evaluated model, both will agree and the benchmark will silently over-score. Cross-family evaluation mitigates but does not eliminate this.

---

## 5. Known Limitations and Threats to Validity

We want this section to be the honest version. None of the following are solved in v1.0.

### 5.1 No Independent Human Validation of Answer Keys
Every `correct_answer` was decided by the authors. There has been no blind second-author review, no independent panel of PMs reviewing the rubrics, and no inter-rater agreement measurement. It is possible — almost certain, at this scale — that some answer keys are wrong or defensibly contested.

**Plan.** (1) Run multi-model cross-validation: any scenario where strong frontier models from different families consistently pick the "wrong" answer gets flagged for author review. (2) Recruit external PMs to blind-validate a stratified sample. (3) Mark scenarios that survive human validation with a `human_validated: true` flag and report sub-scores on the validated subset separately.

### 5.2 Small Author Pool
Two authors. See §3. Community contributions with provenance tags are the planned mitigation.

### 5.3 Single Domain
Every workspace is a software engineering team. PM judgment in healthcare, hardware, growth, or regulated industries has different shapes — different failure modes, different escalation norms, different data to integrate.

**Plan.** We will publish a schema for domain variants and encourage contributed workspaces for at least healthcare PM, hardware PM, and growth PM. Per-domain scores will be reported separately; a global "PM-Bench score" without domain qualification will not be claimed.

### 5.4 Single Workspace (Overfitting Risk)
All 68 MCQ/keyword scenarios share a small set of workspace fixtures in `fixtures/`. The cast of characters is stable, the project names recur, the channel structure is consistent. A model fine-tuned on this workspace would score artificially well. Even without fine-tuning, a model with training data contamination could memorize the workspace.

**Plan.** Procedurally generate workspace variants — same structural scenario, different names, different team structure, different project nouns — so that a correct answer requires the structural reasoning rather than the specific strings. This is a significant piece of v2.0 work.

### 5.5 MCQ Ceiling Effect
Multiple choice tests discrimination, not detection. A model presented with four options may be able to pick the right one even when it would not have generated the right response unprompted. This is a known ceiling: strong models tend to cluster near the top of MCQ benchmarks well before they are actually good at the underlying task.

**Plan.** The open-ended category (§2) is our primary mitigation. Over time we expect the MCQ subscore to become a sanity check and the open-ended subscore to become the headline number.

### 5.6 Contamination
Once PM-Bench is public, future models will see it. This is the same contamination problem every public benchmark has. Scores on frontier models released after the benchmark's publication date should be read with appropriate skepticism.

**Plan.** (1) Maintain a held-out test set that is not published and is only used to validate leaderboard submissions. (2) Periodically refresh questions; track which questions have been in the public set and for how long. (3) Report scores with a "public-since" date on each scenario so consumers can filter.

### 5.7 Scoring Reliability
Keyword scoring is the fragile link (§4.2). MCQ extraction is robust but still fails on hedging responses. LLM-judge scoring has its own stability and bias issues (§4.3). No scoring approach is a ground truth — each is a proxy with known failure modes.

**Plan.** Replace keyword scoring in v2.0. Publish judge-agreement statistics once we have enough open-ended runs to compute them meaningfully.

### 5.8 Prompt Sensitivity
Model responses are sensitive to the system prompt, the way the workspace is delimited, and whether the model thinks it is being tested. The default system prompt in `run.py` is fixed and documented, but scores should be understood as conditional on that prompt. A different harness will produce different numbers.

**Plan.** Publish a "prompt-perturbation" variance report for the default set of frontier models so consumers can see how much of a given score is signal vs. prompt luck.

---

## 6. Reproducibility

PM-Bench aims for bit-reproducible scoring given fixed model outputs, and tight variance on live runs given documented settings.

- **Runner code.** `run.py` is the canonical runner. All scoring is implemented there, not in an external library.
- **Pinned scoring algorithm.** The scorer is committed with the benchmark. Algorithmic changes bump the benchmark version (§10). A score from v1.0 is a score against v1.0's scorer, even if a later version changes the rules.
- **Iterations.** We recommend a minimum of **3 iterations per model** at `temperature=0` (or the provider's equivalent deterministic setting). Report the mean and the per-run scores. If the model cannot be run at temperature 0, report the temperature used and increase iterations to at least 5.
- **Per-scenario logging.** The runner writes, for every scenario, the raw response text, any tool calls observed, the extracted MCQ letter (if applicable), the scoring decision, and the elapsed wall-clock. Submitted results must include this per-scenario detail — an aggregate score with no per-scenario trace is not reproducible and will not be accepted for the leaderboard.
- **Environment.** Report SDK version, model ID, `max_tokens`, temperature, and any non-default system prompt. Results from reasoning-model variants (o1/o3/o4/GPT-5 family) should note the reasoning-budget setting where applicable.

---

## 7. Running the Benchmark Yourself

```bash
# 1. Clone the repository
git clone https://github.com/<org>/pm-bench.git
cd pm-bench

# 2. Install the SDK for your provider (either or both)
pip install anthropic openai

# 3. Set your API key(s)
export ANTHROPIC_API_KEY=...        # for Anthropic models
export OPENAI_API_KEY=...            # for OpenAI models

# 4. Run the Superhuman PM Judgment subset (20 MCQ scenarios)
python run.py --superhuman-only --model claude-sonnet-4-20250514

# 5. Run everything scorable (MCQ + keyword, excludes tool_use)
python run.py --provider anthropic --model claude-sonnet-4-20250514

# 6. Run the open-ended category with an LLM judge
python run.py --open-ended --judge-model gpt-4o

# 7. Run a single scenario by ID for debugging
python run.py --scenario 49 --dry-run
```

Results are written to `results/<timestamp>_<provider>_<model>.json` with full per-scenario detail.

**Submitting to the leaderboard.** Open a PR to `LEADERBOARD.md` that includes: the results JSON, the exact command invoked, the SDK version, the date of the run, and any non-default harness settings. Submissions without per-scenario traces will not be accepted.

---

## 8. Human Baseline Protocol

A human baseline is one of the most valuable things a contributor can add. It anchors the benchmark against the very thing it is trying to approximate — a competent human PM reading the same workspace.

If you want to contribute a human baseline, follow this protocol:

1. **Recruit a participant** who has held a PM or PM-adjacent role in a software org. State their years of experience and domain(s) in the submission; do not collect identifying information beyond that.
2. **Present the workspace.** Show the participant the exact workspace documents from the scenario, rendered as Markdown (or printed), in the same order the runner assembles them. Do not pre-summarize.
3. **Present the trigger without hints.** Do not tell the participant what to look for, what category the scenario is in, or that the scenario is "trying to" test any particular thing.
4. **Time-limit to approximately 5 minutes per scenario.** This matches realistic PM response time to a Slack-shaped trigger. Longer windows inflate human scores in a way that is not representative of how PMs actually operate in a live channel; shorter windows under-measure. Record actual time spent.
5. **Record the raw response verbatim.** No editing, no "what they meant to say." If the participant writes a letter with no explanation, that is the response.
6. **Score with the same rubric as the LLM.** MCQ extraction, keyword match, or LLM-judge rubric — whichever the scenario uses. Do not apply charitable interpretation that the LLM runner would not.
7. **Submit to `HUMAN_BASELINE.md`** as a PR. Include: participant experience band (but no PII), per-scenario time spent, per-scenario raw response, per-scenario scoring outcome, and a short note on scenarios where the participant felt the rubric was wrong. Those notes feed answer-key review (§5.1).

Baselines from a single participant are useful but noisy. If you can run 3+ participants, report mean and per-participant breakdowns.

---

## 9. Comparison to Related Benchmarks

PM-Bench is not a capability benchmark. It is complementary to, not competitive with, the benchmarks below.

- **SWE-bench / SWE-bench Verified.** Measures whether a model can produce a correct code patch given a real GitHub issue and repository. Capability benchmark; ground truth is a passing test suite. PM-Bench measures judgment *about* the engineering work, not the ability to do it. A model could score 0% on SWE-bench and still be a competent PM agent; the reverse is also true.
- **GPQA.** Measures graduate-level domain knowledge in science with adversarially filtered questions. PM-Bench borrows the "expert-authored, adversarially constructed" aesthetic but targets applied judgment in a workplace, not factual recall in a scientific domain.
- **Terminal-Bench.** Measures agentic behavior in a live shell. Capability benchmark for execution. PM-Bench explicitly excludes execution from its construct.
- **EQ-Bench.** Measures emotional reasoning and social understanding. The closest relative to PM-Bench in spirit — both evaluate soft-skill-adjacent judgment — but EQ-Bench is domain-general and dialog-shaped, while PM-Bench is role-specific, workspace-shaped, and artifact-grounded.
- **PRBench / BigCodeBench.** Code-generation benchmarks with test-suite ground truth. Capability, not judgment. Different construct, different failure modes, different scoring.
- **MedXpertQA.** Domain-specific expert-judgment benchmark in medicine; a useful reference for how to structure an expert-authored, role-specific judgment benchmark. PM-Bench is closest to MedXpertQA in methodological posture.

**What PM-Bench adds:** role-specific judgment evaluation in a collaborative environment, grounded in realistic workspace artifacts, with a construct that names the specific forms of inference (joining, detection, calibrated response) it is trying to measure.

**What PM-Bench doesn't attempt:** capability benchmarks in the style of SWE-bench or Terminal-Bench. If you want to know whether a model can *do* the engineering work, run those. PM-Bench tells you whether it reads the room.

---

## 10. Changelog

### v1.0 (2026-04-13) — Initial public release
- 68 MCQ/keyword scenarios across Memory Recall, PM Behavior, and Superhuman PM Judgment (20 scenarios in the Superhuman category).
- 5 context-assembly experiments, reported separately.
- 20 open-ended scenarios with LLM-judge rubrics (being added; judge protocol finalized).
- `extract_mcq_choice` with 17-case self-test, committed in `run.py`.
- Keyword scoring with documented fragility.
- Single workspace, two-author scenario pool, no independent human validation.

### Planned for future versions
- **Scenario additions/removals.** Item analysis on collected results will identify scenarios that are either trivially passed by all models (no discrimination) or failed by all models (possibly broken or unfair). These get removed or rewritten with version bumps.
- **Scoring algorithm updates.** Keyword scoring replacement (§4.2). Any algorithmic change ships as a new benchmark version; results reported against an older version remain labeled with that version.
- **Workspace variants.** Procedurally generated alternates of the existing workspace for anti-memorization (§5.4).
- **Domain variants.** Healthcare PM, hardware PM, growth PM workspaces with their own scenario sets (§5.3).
- **Held-out test set.** A private split to validate leaderboard submissions against contamination (§5.6).
- **Human baseline dataset.** Aggregated `HUMAN_BASELINE.md` from contributor submissions (§8).

Scores reported against one version of the benchmark should not be compared directly to scores reported against another. The version tag on the runner is authoritative.

---

*Questions, disagreements about answer keys, proposed scenarios, and human-baseline submissions are welcome as GitHub issues and PRs.*
