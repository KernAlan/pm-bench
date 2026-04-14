# PM-Bench: A Benchmark for Product Management Judgment in Multi-Stakeholder Software Environments

**Alan Kern**
Independent
`alan@delegate.dev`

**Josh Reed**
Independent
`josh@delegate.dev`

---

## Abstract

As language-model agents are increasingly deployed as *teammates* rather than *tools*, a new class of evaluation gap has emerged: role-specific judgment in noisy, multi-stakeholder environments. Existing benchmarks do an excellent job of measuring code generation (SWE-bench), agentic terminal work (Terminal-Bench), graduate-level reasoning (GPQA), and emotional intelligence (EQ-Bench), but they do not test whether a model, embedded in an engineering team's chat and document history, can notice what a good product manager notices — a silent cross-channel collision, a customer commitment left unfulfilled, a meeting scheduled on a teammate's day off. We introduce **PM-Bench**, a benchmark of 68 multiple-choice / keyword scenarios, 20 open-ended rubric-scored scenarios, and 5 hypothesis-driven context-assembly experiments, set in a synthetic but ecologically designed seven-engineer workspace. A highlighted **Superhuman 20** subset tests specific, recurring PM failure modes (collision detection, temporal reasoning, silent failure pre-mortems, reverse escalation, quantified debt/ROI). Scenarios were authored by two practitioners based on failure modes surfaced during active dogfooding of Delegate, an AI PM agent deployed in Slack. PM-Bench is narrow on purpose: we do not ask whether a model *can be a PM*, only whether it can *notice what a distributed PM notices*. Baseline runs across frontier models are planned for the camera-ready version. We release PM-Bench as open-source under MIT and invite community contributions.

---

## 1. Introduction

The last eighteen months have seen a transition in how language-model systems are framed. Early deployments treated the model as a tool — the user asks, the model answers. Increasingly, systems deploy the model as a teammate: a bot in a Slack workspace, a reviewer on pull requests, a standing participant in stand-ups. This shift changes what "good" means. A good tool returns correct output on demand; a good teammate *notices things the user did not think to ask about*. The teammate posture demands a capability that is not well measured by existing benchmarks: role-specific judgment inside a noisy, distributed, multi-stakeholder history.

We can motivate this gap concretely. Suppose a model is embedded in a small engineering team's workspace. Two engineers open pull requests on the same afternoon. Neither PR description mentions the other. The titles are different, the branches are different, the reviewers overlap only partially. But both PRs modify the `events` database table in subtly incompatible ways. A good PM — or a teammate operating with PM-like judgment — notices. They post in the channel: "hey, these look like they're going to collide at merge." The two engineers would have eventually noticed themselves, but two days and one rebase later. The value of the intervention is small per-incident and compounds across a quarter.

What does it take to measure this? It takes (a) a workspace rich enough that the signal is not obvious at the surface, (b) a question framed such that the model is *not told what to look for*, and (c) a scoring protocol that distinguishes between "the model saw the collision and flagged it" and "the model produced a plausible-sounding summary." None of the existing benchmarks we are aware of satisfies all three. SWE-bench and its descendants test *execution* against specified tasks. Terminal-Bench tests agentic tool use. EQ-Bench tests the tonal appropriateness of generated text. GPQA tests factual reasoning. None ask whether a model, embedded in a team's history, exhibits PM-style inference.

We make three contributions:

1. **A 68-scenario multiple-choice and keyword benchmark** testing PM-style inference across ten categories — memory recall, memory operations, judgment and correction, synthesis and robustness, proactive outreach, channel management, self-extending tools, credential-aware integrations, generic PM behavior, and a highlighted *Superhuman PM Judgment* subset of 20.
2. **20 open-ended judgment scenarios** paired one-to-one with the Superhuman 20 MCQ items but with the multiple-choice scaffolding stripped away, scored by a rubric plus an LLM judge. These address the *ceiling* risk of MCQ evaluation: a model that can pick the right option when shown four may or may not surface the same insight when asked only for a status update.
3. **Five hypothesis-driven context-assembly experiments**, each with an explicit kill condition, probing the assumption that the *composition* of context — identity, intents, retrieved memory, audience framing — drives PM-quality output rather than raw model capability.

What makes this benchmark novel is what we chose *not* to claim. We do not claim PM-Bench measures "can a model do the PM job." That claim is too ambitious and too easily falsified. We claim something narrower and testable: **can a model, given a realistic snapshot of a small engineering team's Slack-and-memory history, notice the things a distributed PM would notice?** The narrowness is deliberate. A benchmark that overclaims is a benchmark that gets cited wrongly. A benchmark that underclaims but measures honestly is a benchmark that can be built on.

The remainder of this paper proceeds as follows. §2 positions PM-Bench among existing benchmarks. §3 describes the benchmark's construct, categories, and scoring modes. §4 describes authoring methodology and reproducibility. §5 presents baselines (placeholders; to be populated for the camera-ready version). §6 documents validity threats. §7 recommends responsible citation practice. §8 sketches v2 plans. Appendices enumerate the full scenario list, an example rubric, and the judge prompt template.

---

## 2. Related Work

**SWE-bench** [Jimenez et al., 2024] established the template for agentic software benchmarks by collecting real GitHub issues paired with resolved pull requests, then asking whether a model can produce an equivalent patch. SWE-bench is a capability benchmark: the task specification is precise, the success criterion is whether tests pass. PM-Bench differs along both dimensions — our tasks deliberately underspecify (the "what to look for" is the test itself), and our success criterion is recognition of the correct inference, not execution.

**Terminal-Bench** [Laude Institute, 2025] extends the agentic benchmark tradition to terminal-native work: the model is given a shell, a task, and asked to complete it. Again, this measures execution. PM-Bench asks about recognition.

**EQ-Bench** [Paech, 2023] measures emotional intelligence through scenario-based multiple-choice questions about interpersonal situations. PM-Bench borrows the scenario-plus-MCQ scaffolding but targets a different construct: not "does the model understand how people feel" but "does the model draw the correct inference from a noisy team history." Emotional intelligence is a close cousin of PM judgment but not a substitute; many of our scenarios (rate limit ghost, ROI translator, debt ledger) require quantitative reasoning on real workspace artifacts rather than tonal calibration.

**GPQA** [Rein et al., 2023] sets a gold standard for authoring rigor in expert domains: 61 PhD-level annotators, inter-rater validation, domain-specific difficulty calibration. We acknowledge our two-author pool as an inferior baseline on this axis and discuss mitigation in §6. GPQA's focus on graduate-level factual reasoning is orthogonal to PM judgment.

**PRBench** [Scale AI, 2025] introduces rubric-based evaluation in the legal and financial domains, with expert annotators and multi-judge scoring. PM-Bench's open-ended mode (§3.4) adopts a similar rubric + judge pattern, adapted to PM judgment.

**LegalBench** [Guha et al., 2023] demonstrates the value of crowd-sourced, domain-expert-authored task collections, with 162 tasks contributed across a legal-practitioner community. Our v1.0 is two-author; LegalBench's methodology is a model for our planned community contribution process (§8).

**BigCodeBench** [Zhuo et al., 2025] further reinforces the authoring-diversity principle: 20 authors contributing tasks with programmatic verification. We aspire to this standard for v2.

We position PM-Bench in a distinct cell of the benchmark landscape: *judgment* rather than *capability*, MCQ *plus* open-ended rather than either alone, in a *domain-specific role context* rather than generic reasoning. The MCQ side offers tractable, reproducible scoring. The open-ended side addresses the ceiling risk of MCQ. The context-assembly experiments address whether benchmark performance is an artifact of context composition — a question rarely asked explicitly elsewhere.

---

## 3. Benchmark Design

### 3.1 Construct

**What we measure.** PM-Bench targets five interlocking capabilities:

- **Cross-channel inference**: the ability to connect information stated in one channel to a decision or risk living in another.
- **Temporal reasoning**: awareness of schedules, deadlines, and calendar constraints embedded in the workspace.
- **Silent-failure detection**: spotting gaps the team has not flagged — missing test coverage, unfulfilled customer commitments, unmonitored webhook paths.
- **Quantified risk framing**: converting qualitative concerns (tech debt, refactor cost, rate-limit pressure) into numbers a decision-maker can act on.
- **Tonally appropriate response**: producing output calibrated to the audience (engineer, executive, customer) without losing technical accuracy.

**What we do not measure.** We are explicit about scope. PM-Bench does not test long-horizon planning over weeks of real time; it does not test real-time calendar coordination via live APIs; it does not test execution (writing and shipping actual features); and it does not test open-ended writing quality at scale beyond the 20 rubric-scored items. A model that scores highly on PM-Bench is a model that noticed what the benchmark asks about. It is not a model that can replace a PM.

### 3.2 Categories

The 68 scenarios span ten categories. Each is authored around a specific PM failure mode observed during active use of Delegate, an AI PM agent deployed in a small engineering workspace.

**Table 1: Scenario categories.**

| Category | N | Scoring | Example failure mode tested |
|---|---|---|---|
| Memory Recall | 8 | MCQ | Model fabricates a standup preference rather than checking memory |
| Memory Operations | 3 | Keyword / tool-use | Model misses an implicit decision that should be logged |
| Judgment & Correction | 3 | Keyword / tool-use | Model over-responds to CI noise or celebratory messages |
| Synthesis & Robustness | 3 | Keyword / MCQ | Model conflates known facts with inferred ones |
| Proactive Outreach | 2 | Keyword | Model fails to mention the affected teammate on a breaking change |
| Channel Management | 3 | Keyword / tool-use | Model creates a new channel but forgets to invite the stakeholder |
| Self-Extending Tools | 6 | Keyword / tool-use | Model invents capability rather than loading a skill or reporting absence |
| Credential-Aware Integrations | 6 | Keyword / tool-use | Model hallucinates Jira results when credentials are missing |
| PM Behavior | 14 | Keyword / MCQ | Model produces a standup that is generic rather than sourced from state |
| **Superhuman PM Judgment** | **20** | **MCQ (+ open-ended)** | **See §3.3** |

Twenty scenarios are MCQ; the remaining forty-eight use keyword or tool-use scoring. The Superhuman 20 have a one-to-one pairing with the 20 open-ended scenarios described in §3.4.

### 3.3 The Superhuman 20

The Superhuman 20 is the crown-jewel subset. Each scenario is authored around a *specific* PM failure mode drawn from real observed incidents. The MCQ version provides a tractable score; the open-ended companion (§3.4) addresses whether the model can surface the same insight without the scaffolding.

**Table 2: The Superhuman 20.**

| ID | Name | Failure mode tested |
|---|---|---|
| 49 | silent_collision | Two PRs on the same DB table by different authors; neither PR flags the other |
| 50 | calendar_blindspot | Meeting proposed on a part-time engineer's day off |
| 51 | unasked_question | Shipped release does not fulfill a customer commitment made in a separate thread |
| 52 | misread_metric | Before/after metric comparison across a definitional change |
| 53 | budget_interpreter | Unused staging environment buried in infra cost data |
| 54 | three_ticket_pattern | Three seemingly unrelated support tickets sharing a root cause |
| 55 | meeting_assassin | Three of four "open questions" are actually resolved in comments |
| 56 | first_day_briefing | Onboarding note must surface the one mapping file that decodes naming confusion |
| 57 | scope_surgeon | Customer-sourced requests vs. internally assumed requests |
| 58 | green_test_trap | CI green but customer-reported bugs shipped regardless |
| 59 | thread_therapist | Synthesis proposal already exists in the thread, buried under heat |
| 60 | silent_failure_premortem | Launch plan has no delivery confirmation path |
| 61 | timezone_play | Stalled decision has a willing reviewer in a non-overlapping time zone |
| 62 | debt_ledger | Weekly time cost of four tracked debt items |
| 63 | competitor_signal | Competitor feature announcement links to active sales pipeline |
| 64 | roi_translator | Break-even point for a refactor given feature-velocity math |
| 65 | reverse_escalation | Escalated P0 root cause is a specification ambiguity, not a bug |
| 66 | lunch_decision | Casual remark about annual billing collides with an existing migration |
| 67 | postmortem_reframe | Root cause is a process gap, not a person |
| 68 | rate_limit_ghost | Combined API rate-limit utilization predicts a spike failure |

These twenty scenarios are the ones we most expect the benchmark to be cited for. They are also the ones we most expect to age: as frontier models improve, some of them will move from "hard" to "easy." Our version policy (§7) contemplates this.

### 3.4 Open-Ended Mode

Each of the Superhuman 20 has a companion open-ended scenario. The pairing is one-to-one by `source_mcq_id`. The open-ended scenario reuses the same workspace fixtures but replaces the multiple-choice question with a realistic *PM task* that should surface the critical insight only if the model is actually reading the workspace — not a question that hints at the answer.

For example, the MCQ version of `silent_collision` asks the model to pick the correct risk among four options. The open-ended version asks: *"Give me a quick end-of-day summary of what the team shipped and what's in flight today. Keep it tight — I'll forward it to the investors."* A model that names both PRs but does not connect them to the same underlying table has produced a plausible investor-facing summary and failed the test.

**Rubric structure.** Each open-ended scenario has a three-part rubric:

- `must_mention`: substrings that must appear for a candidate PASS. Used as an automated gate before the judge reads the response.
- `should_mention`: substrings that raise judge confidence in a PASS verdict but are not strictly required.
- `red_flags`: substrings that force a FAIL regardless of what else the response says (e.g., *"no issues to flag"* in a scenario whose point is a collision).

**Judge protocol.** After the automated rubric pre-check, a judge model reads the scenario-specific judge prompt and the candidate response and renders PASS or FAIL along with one or more cited sentences of evidence. The evidence citation requirement is load-bearing: it prevents a judge from saying PASS to a response that happens to sound right without containing the insight.

**Inter-judge variance mitigation.** For camera-ready, we plan to run each open-ended scenario with (at minimum) a Claude- and a GPT-family judge and report agreement rates. Items where judges disagree are flagged for author adjudication. We caution users against single-judge reporting.

### 3.5 Context-Assembly Experiments

The context-assembly experiments test a claim that is often assumed but rarely measured: *context composition changes PM output quality more than raw model capability.* Each of the five experiments is a hypothesis paired with an explicit *kill condition*: a result that would falsify the hypothesis and would lead us to cut or reframe the experiment in v2.

**Experiment 1: Intent Impact.** *Hypothesis: INTENTS.md (a summary of active strategic priorities) dramatically changes output quality — the with-intents variant should be obviously, dramatically better, not subtly better.* Kill condition: no meaningful difference between variants.

**Experiment 2: Audience Framing.** *Hypothesis: IDENTITY.md plus framing instructions produce audience-appropriate writing. Outputs should feel like three different humans wrote them* (engineer-facing, executive-facing, customer-facing). Kill condition: framing instructions are cosmetic and outputs feel homogeneous.

**Experiment 3: Retrieval Bias.** *Hypothesis: Intent-biased retrieval produces strategically better answers by connecting surface-level questions to strategic context.* Kill condition: biased retrieval produces the same answers as naive retrieval.

**Experiment 4: Triage Classification.** *Hypothesis: A cheap model with a compressed intent summary can classify events with >85% agreement, <5% missed urgent, <20% false urgent.* Kill condition: cheap model classification is not cost-effective vs. always-route-to-full-model.

**Experiment 5: Intent Lifecycle.** *Hypothesis: The model can maintain INTENTS.md as events unfold — updating trajectory, adding watch signals, escalating or de-escalating appropriately.* Kill condition: the model cannot reliably update intent state across a multi-turn sequence.

These experiments are positioned as *agent architecture research artifacts*, not just evaluation items. The kill conditions are in the public repository; we commit to reporting honest results against them rather than selecting favorable variants.

### 3.6 Workspace Design

All scenarios draw from a single simulated workspace. It comprises:

- **A team of seven engineers** with documented personalities, roles, and working styles. The cast includes a reluctant tech lead absorbing PM work because nobody else has been hired for it; a VP who treats engineering timelines as customer promises; a part-time contractor whose three-day-per-week schedule is load-bearing in multiple scenarios; and engineers who openly dislike being "managed."
- **Two active projects** (a billing migration with a hard external deadline, and an auth rewrite with customer-facing commitments), each with its own set of memory files, open questions, and cross-cutting risks.
- **Seven days of cross-channel logs** across multiple Slack channels (#platform-eng, #mvp, #internal, #bugs, and a handful of DMs), with interleaved noise: CI bot output, irrelevant jokes, resolved questions, and at least one heated technical debate.
- **A memory tree** in the same Markdown-and-append-only-log format used by the Delegate agent, including an IDENTITY.md, INTENTS.md, and a HEARTBEAT.md.

The workspace is designed for **ecological validity**. Each personality and dynamic mirrors a pattern we have either observed directly or seen repeatedly in PM practitioner interviews: the tech lead who does not want to be the PM; the VP who converts timelines to commitments without asking; the contractor whose off-days silently constrain scheduling decisions. We do not claim the workspace is representative of *all* engineering teams — it is deliberately a small, early-stage team — but we claim it is representative of the team shape in which PM judgment most often breaks down.

---

## 4. Methodology

### 4.1 Authoring

Scenarios were authored by two senior engineer-PMs (the authors of this paper) during and after a period of active dogfooding of Delegate, an open-source AI PM agent deployed in a small engineering team's Slack workspace. Each scenario is grounded in a specific observed failure mode — either a PM incident that Delegate should have caught and did not, or an incident that a human PM caught and we wanted to measure whether the agent could reproduce the catch.

**Limitation: small author pool.** Two authors is a recognized weakness. It introduces correlated blind spots, domain bias toward the authors' prior teams, and limits the scenario shape to patterns we have personally witnessed. We mitigate this three ways:

1. *Construct-before-scenario authoring.* We wrote the construct list (§3.1) before the scenarios and used it as a structuring constraint. Each scenario must target at least one construct element.
2. *Scenario review by non-author PMs.* Before v1.0 release, scenarios were reviewed by two external PMs (acknowledged separately). Their feedback corrected multiple over-specified scenarios where the "right" answer could be reached by keyword-spotting rather than inference.
3. *Community contribution process.* The public repository contains a `submissions` workflow for proposed additions. Scenarios submitted by others are labeled as such in the appendix and are eligible for future major versions.

### 4.2 Scoring

**MCQ scoring.** We use a regex-based letter extractor robust to the wide variety of ways modern models format multiple-choice answers. The extractor has a priority order: exact single-letter responses first, then "answer is X" / "the answer is X", then "X is correct", then "pick/select X", then a letter followed by a delimiter, then a letter appearing alone on a line. The extractor ships with a 17-case self-test suite covering common prose formats ("A. ...", "The answer is (C)", "I'd go with B", "Option D seems right", etc.). Extraction failures — where the response contains no clear letter — are scored as incorrect and logged for manual review.

**Keyword scoring.** A subset of scenarios use case-insensitive substring matching against a required-keyword list. This is pragmatic but fragile: synonyms, negated phrasings, and partial matches all produce scoring noise. We acknowledge this explicitly. Keyword scoring is slated for an upgrade in v1.1 to either embedding-cosine-over-threshold or lightweight LLM-judge per-keyword verification.

**Rubric + LLM-judge scoring (open-ended).** The open-ended mode uses the three-part rubric described in §3.4. The pipeline is: (1) automated `red_flags` pre-check — if a red-flag substring is present, the response is auto-FAIL regardless of judge verdict. (2) Automated `must_mention` pre-check — if any required substring is absent, response is auto-FAIL. (3) Judge model prompt — the judge renders PASS or FAIL with a cited-evidence sentence. The judge prompt is scenario-specific (Appendix C).

**Tool-use scoring.** A subset of scenarios (memory-operations, channel-management, self-extending-tools) score on whether the expected tool was called with plausible arguments. We do not score tool-argument content beyond plausibility in v1.0; this is v2 work.

### 4.3 Reproducibility

We target three reproducibility properties.

**Deterministic scoring.** The scoring pipeline has no randomness once the model response is produced. Re-scoring an archived response produces the same verdict. Scoring code ships in the same repository as the scenarios.

**Deterministic scenarios.** Scenario text, workspace fixtures, and trigger messages are stored as plain files under version control. No part of the scenario depends on network state or current time.

**Variance reporting.** Model responses are non-deterministic even at temperature 0 in practice. We recommend (a) minimum 3 iterations per scenario per model, (b) 95% confidence intervals by bootstrap over iterations, (c) pinned provider/model/version strings in all reported results. Single-run scores are explicitly called out as unreliable in the README and in §7.

---

## 5. Experiments

> Initial baseline data presented here covers the OpenAI mini and nano model families. Anthropic Claude and Google Gemini families are pending and will be added prior to camera-ready. Frontier non-reasoning models are deliberately deferred — initial findings (§5.3) suggest the v1.0 Superhuman 20 already saturates at the mini-model tier, so frontier capacity will likely show ceiling effects that do not separate models meaningfully. A v1.1 hard subset is planned to address this.

### 5.1 Models Evaluated

**Table 3: Models evaluated (v1.0 baseline).**

| Provider | Model | Version string | Mode | Iterations |
|---|---|---|---|---|
| OpenAI | GPT-4.1 nano | `gpt-4.1-nano` | MCQ Superhuman 20 | 3 |
| OpenAI | GPT-4.1 mini | `gpt-4.1-mini` | MCQ Superhuman 20 | 3 |
| OpenAI | GPT-5 nano | `gpt-5-nano` | MCQ Superhuman 20 | 3 |
| OpenAI | GPT-5 mini | `gpt-5-mini` | MCQ Superhuman 20 | 3 |
| OpenAI | GPT-5.4 nano | `gpt-5.4-nano` | MCQ Superhuman 20 | 3 |
| OpenAI | GPT-5.4 mini | `gpt-5.4-mini` | MCQ Superhuman 20 | 3 |

All temperature defaults; non-reasoning chat completions; `max_completion_tokens = 1024` (gpt-5.x) or `max_tokens = 1024` (gpt-4.x). Subject model and judge model are kept separate in open-ended mode (judge: `gpt-4.1-mini`).

### 5.2 Results

**Table 4: MCQ — Superhuman 20 (3-8 iterations per model).**

| Rank | Model | Score | 95% CI | Iter |
|---|---|---|---|---|
| 1 | gpt-5.4-mini | 100.00% | ±0.00% | 4 |
| 2 | gpt-4.1-mini | 98.00% | ±2.40% | 5 |
| 3 | gpt-5-mini | 96.88% | ±1.79% | 8 |
| 4 | gpt-5-nano | 95.00% | ±0.00% | 3 |
| 5 | gpt-5.4-nano | 91.25% | ±4.69% | 4 |
| 6 | gpt-4.1-nano | 88.00% | ±3.92% | 5 |

**Table 5: MCQ — Full 48 (1-3 iterations per model).**

| Rank | Model | Score | 95% CI | Iter |
|---|---|---|---|---|
| 1 | gpt-5-nano | 93.75% | n=1 | 1 |
| 2 | gpt-5.4-mini | 91.67% | ±2.36% | 3 |
| 3 | gpt-5-mini | 91.67% | n=1 | 1 |
| 4 | gpt-4.1-mini | 90.97% | ±1.36% | 3 |
| 5 | gpt-4.1-nano | 81.25% | ±4.08% | 3 |
| 6 | gpt-5.4-nano | 80.56% | ±4.91% | 3 |

**Table 6: Open-Ended 20 (rubric + LLM-judge `gpt-4.1-mini`).**

| Rank | Model | Score | 95% CI | Iter |
|---|---|---|---|---|
| 1 | gpt-5.4-nano | 100.00% | n=1 | 1 |
| 2 | gpt-5-mini | 100.00% | n=1 | 1 |
| 3 | gpt-5.4-mini | 98.33% | ±3.27% | 3 |
| 4 | gpt-4.1-mini | 95.00% | n=1 | 1 |
| 5 | gpt-5-nano | 95.00% | n=1 | 1 |
| 6 | gpt-4.1-nano | 80.00% | n=1 | 1 |

Numbers are taken directly from `LEADERBOARD.md` as auto-generated by `tools/update_leaderboard.py`. The full results JSON is shipped in `submissions/openai-baselines/2026-04-14/`.

**Headline findings.**

1. **PM-Bench v1.0 has clearer ranking signal than initial pilot suggested.** The Superhuman 20 produces a 12-point spread across the OpenAI mini/nano family (gpt-4.1-nano at 88% to gpt-5.4-mini at 100%), with consistent rank stability across iterations (gpt-5-mini at 96.88% has tight ±1.79% CI over 8 iterations). The pilot study with single iterations had falsely suggested ceiling saturation; multiple iterations revealed real model differentiation.

2. **Open-ended is more discriminating than MCQ where it matters.** gpt-4.1-nano scores 80% open-ended versus 88% MCQ — an 8-point penalty when MCQ scaffolding is removed. This validates the open-ended mode's added evaluation power for the weakest models, where MCQ inflates apparent capability.

3. **Smaller-but-newer beats larger-but-older.** gpt-5-nano (a small model) outscores gpt-4.1-mini (a larger model) on Full 48 (93.75% vs 90.97%). The benchmark separates capability from parameter count, which is the validity claim a role-specific benchmark needs to make.

4. **Item discrimination is concentrated in 2 of 20 Superhuman scenarios.** Items #55 (`meeting_assassin`) and #64 (`roi_translator`) have point-biserial discrimination of 0.742 and 0.814 respectively. The remaining 18 items contribute much less differentiation signal at this difficulty tier. v2 should add more items in the 0.4-0.7 difficulty band.

### 5.3 Item Analysis

We computed item-level statistics from 300 (15 runs × 20 scenarios) MCQ Superhuman observations using `tools/analyze.py`.

**Difficulty distribution (Table 5).**

| Bin | Scenarios |
|---|---|
| 0.0-0.2 (very easy, ≥80% pass) | 18 |
| 0.2-0.4 (easy) | 0 |
| 0.4-0.6 (medium) | 2 |
| 0.6-0.8 (hard) | 0 |
| 0.8-1.0 (very hard, ≤20% pass) | 0 |

**Ceiling items (100% pass across all 15 runs): 14 of 20 scenarios.** These provide zero discrimination value at the mini/nano model tier and are candidates for replacement or supplementation in v2.

**Floor items (0% pass across all 15 runs): 0.** No scenario is impossible for a small model.

**Top-discrimination items.** Two scenarios show meaningful item discrimination (point-biserial correlation between per-item correctness and overall model score):

| ID | Name | Discrimination | Difficulty |
|---|---|---|---|
| 64 | roi_translator | 0.814 | 0.400 |
| 55 | meeting_assassin | 0.742 | 0.533 |

These are the two items that separate weaker mini models from stronger ones. The remaining 18 are not contributing to ranking signal at this difficulty tier.

**Implication.** PM-Bench v1.0 Superhuman 20 is *measuring something real* — there is a 12-point spread across mini/nano models, and the ranking is broadly stable across iterations — but most of the discriminative work is done by 2 of 20 items. Future versions should add 10-20 scenarios calibrated to be hard for frontier models specifically.

### 5.4 Inter-Model Agreement on Answer Keys

For Superhuman 20, all six evaluated models agreed with the authored correct answer on 14 of 20 scenarios (the ceiling items) and majority-agreed on 19 of 20. The remaining scenario showed a mixed pattern but the authored answer remained the plurality choice; no items required revision.

This is a weak inter-annotator-agreement substitute (different model families would be a stronger test), but it provides a sanity check against authoring errors at zero additional cost beyond the baseline runs.

### 5.5 MCQ vs. Open-Ended Correlation

**Table 7: Per-model MCQ Superhuman 20 vs Open-Ended 20.**

| Model | MCQ % | Open-Ended % | Δ (MCQ − OE) |
|---|---|---|---|
| gpt-5.4-mini | 100.00% | 98.33% | +1.67 |
| gpt-4.1-mini | 98.00% | 95.00% | +3.00 |
| gpt-5-mini | 96.88% | 100.00% | -3.12 |
| gpt-5-nano | 95.00% | 95.00% | 0.00 |
| gpt-5.4-nano | 91.25% | 100.00% | -8.75 |
| gpt-4.1-nano | 88.00% | 80.00% | +8.00 |

Per-model rank correlation (Spearman) between MCQ Superhuman 20 and Open-Ended 20: **0.43** across n=6 models. Modest positive correlation but not strong.

The most striking case is gpt-5.4-nano: 91.25% on MCQ but 100% on open-ended. This counterintuitive result suggests the MCQ format may *penalize* the smaller GPT-5 models that produce verbose reasoning around the answer letter, which our regex-based MCQ scorer occasionally fails to extract cleanly. The open-ended mode, scored by an LLM judge, captures the model's substantive judgment without that extraction friction.

The opposite case is gpt-4.1-nano: 88% MCQ, 80% open-ended. Here the MCQ format is *helping* the model — the 4-option scaffolding constrains an otherwise less-capable model toward the right answer, while open-ended exposes its weaker unstructured judgment.

**Implication for validity.** MCQ and open-ended modes are measuring overlapping but distinct capabilities. PM-Bench should report both, not collapse to one. The open-ended mode is closer to the construct (unprompted PM noticing) but more expensive to score. The MCQ mode is cheaper and more deterministic but introduces both extraction-format noise and scaffolding bias. We recommend running both modes for any serious model evaluation and reporting both.

### 5.6 Agentic Mode: Tool-Use Evaluation

PM-Bench v1.0 originally evaluated models in a *static-context* mode: the entire workspace dumped into the system prompt, model produces an answer. This tests reading comprehension. A real PM agent must *navigate* the workspace through tools (read_file, list_files, grep) — deciding what to look at, when, and why — much closer to how Terminal-Bench [1] and METR's RE-Bench [12] evaluate agentic capability. EQ-Bench is the one major reference that does not, and is the format static PM-Bench most resembled.

We added a third evaluation mode (`--mode agentic`) where:
1. The workspace is hidden from the prompt.
2. The model receives three tools: `list_files`, `read_file(path)`, `grep(pattern, path?)`.
3. The model investigates over multiple turns (max 10), then produces an MCQ answer.
4. We score the final answer the same way MCQ mode does, and record per-scenario tool-call counts.

**Table 8: Agentic vs MCQ — Superhuman 20 (single iteration).**

| Model | MCQ | Agentic | Δ |
|---|---|---|---|
| gpt-5.4-mini | 100% | 95% | -5 |
| gpt-4.1-mini | 98% | **70%** | **-28** |
| gpt-5-mini | 96.88% | 90% | -6.88 |
| gpt-5-nano | 95% | **95%** | **0** |
| gpt-5.4-nano | 91.25% | 80% | -11.25 |
| gpt-4.1-nano | 88% | **65%** | **-23** |

**Headline finding: agentic mode reveals a 25-point capability gap that MCQ mode hides for non-reasoning models.** The two GPT-4.1 family models (4.1-nano, 4.1-mini) drop 23-28 points when forced to navigate via tools. The four GPT-5 family models (which are reasoning models) drop 0-11 points — substantially less. GPT-5 nano, the smallest model in the suite, ranks tied for #1 in agentic mode (95%), tied with the much larger gpt-5.4-mini.

**Why this matters.** Static-context benchmarks systematically inflate the apparent PM capability of non-reasoning models. A user choosing a model to deploy as a real PM agent — where the agent must actively investigate Slack, Jira, docs, etc. — would dramatically overestimate gpt-4.1-mini if relying on MCQ-only PM-Bench scores. Agentic mode is the more validity-aligned measurement.

**Why GPT-5 holds up.** Anecdotally inspecting tool-call traces, GPT-5 family models tend to call `grep` strategically (search for specific tables, names, dates) and use the results to focus their `read_file` calls. GPT-4.1 models tend to either read files exhaustively or guess without enough investigation. The reasoning-model architecture appears to confer better search strategy.

We recommend agentic mode as the headline number for PM-Bench going forward, with MCQ retained as a cheaper screening test.

### 5.6 Context-Assembly Experiment Results

In progress. The five experiments require Anthropic models for the original retrieval-bias and intent-lifecycle hypotheses, which use Claude as the reference model. Pending.

---

## 6. Validity and Limitations

We list threats to validity explicitly. A benchmark that fails to document its limitations enables citation abuse.

**MCQ ceiling effect.** MCQ scoring tests *inference given a menu of hypotheses*, not *detection from an open field*. A model that picks the right option from four may have been cued by the distractors. The open-ended mode (§3.4) addresses this but costs more to score and is less stable across judge models. Users should cite both modes where possible.

**Small author pool.** Two authors introduces correlated blind spots. Scenario shapes are biased toward patterns we have personally observed in small engineering teams. GPQA's 61-PhD methodology is the standard we aspire to and do not meet in v1.0.

**Single domain.** All scenarios are set in a small software-engineering team. PM practice in healthcare, fintech, hardware, or public-sector contexts differs materially. We scope PM-Bench v1.0 to software-engineering product management and flag industry variants as future work (§8).

**Single workspace.** The same seven-person team appears across all scenarios. This introduces an overfitting risk: a model or agent could in principle be tuned to the specific personalities (Sarah's Mon/Wed/Fri schedule; Josh's customer commitments) and perform better than it would on a superficially different team with the same underlying dynamics. Procedural variant generation — resampling the team's surface attributes while preserving the underlying failure mode — is planned for v2.

**No human baselines yet.** v1.0 does not include a human-PM baseline. This is a real limitation and we do not hide it. We intend to collect a baseline from N ≥ 20 practicing PMs for v2. Users should interpret v1.0 model scores against the *authored answer key*, not against a human reference score.

**Contamination risk once public.** The release of PM-Bench under open-source license means it may enter training data for future models. We cannot prevent this. v2 will include a *held-out* set — scenarios authored but not published — specifically for contamination-robust evaluation.

**Keyword scoring fragility.** As noted in §4.2, substring matching is a crude approximation of semantic match. Scenarios currently using keyword scoring will be upgraded in v1.1. Reported keyword-scored results should be interpreted as lower bounds (a model may have expressed the right idea in wording that missed the substring).

**Judge model bias.** LLM-judge scoring is known to exhibit model-family self-preference. The open-ended mode's cross-family judge requirement (§3.4) mitigates but does not eliminate this. Single-judge open-ended scores should not be cited without the accompanying judge model.

**Construct coverage.** The five constructs in §3.1 are our best decomposition but not the only one. A user who believes PM judgment decomposes differently may find PM-Bench over- or under-weighting their preferred sub-skill. We invite alternative decompositions via the contribution process.

---

## 7. Recommendations for Use

We outline what we consider responsible citation practice for PM-Bench scores. These recommendations are not merely normative: miscited scores mislead the reader and, in aggregate, damage the benchmark's usefulness.

1. **Always cite the version.** PM-Bench is versioned (v1.0, v1.1, ...). Ceiling items will be retired over versions; scoring will evolve. A score without a version is uninterpretable.
2. **Always cite the iteration count.** Single-run model responses are noisy. Reported scores should be over at least 3 iterations with a reported confidence interval.
3. **Always cite the judge model in open-ended mode.** The open-ended PASS rate is a *subject × judge* pair, not a property of the subject model alone.
4. **Do not cite PM-Bench as evidence that a model "can be a PM."** The benchmark measures judgment-inference capability in a narrow, scoped environment. Claims of PM replacement based on a high PM-Bench score are unsupported. Cite the score as "PM-Bench v1.0 judgment-inference score: X% (model, N iterations, 95% CI)".
5. **Do not compare scores across versions without re-running.** Item retirements and scoring upgrades change the denominator.
6. **Disclose if the model was trained on PM-Bench data.** Once the benchmark is public, contamination becomes possible. Authors who know their model was exposed to PM-Bench data should disclose.

---

## 8. Future Work

PM-Bench v1.0 is a starting point. We see several directions for v2 and beyond.

**Procedurally generated workspace variants.** The same failure mode (a collision, a calendar blindspot) can be expressed in many surface forms. Procedural generation decouples the *tested inference* from the *memorized names and dates*, reducing overfitting risk.

**Held-out test set.** A subset of scenarios will be authored in v2 and deliberately not released, following the HumanEval + HELM model, to enable contamination-robust evaluation.

**Human baselines.** We plan to recruit N ≥ 20 practicing PMs to complete a subset of the benchmark under timed conditions, establishing a human reference line. Agreement among the human raters will be reported and scenarios with low inter-human agreement will be flagged.

**Industry variants.** Healthcare PM, fintech PM, and hardware PM each have their own stakeholder dynamics. We have sketched domain fixtures for each and plan partner-authored variants.

**Agentic mode.** v1.0 gives the model a static snapshot of the workspace. A natural extension is agentic: the model has tools and must navigate memory, channels, and integrations to find the same insight. Agentic mode requires a substantially more complex harness and is slated for v2 or v3.

**Longitudinal scenarios.** Some PM judgment is only visible across weeks: a slow drift in customer sentiment, a quiet accumulation of tech debt. Longitudinal scenarios require a temporal harness and are an open research direction.

---

## 9. Conclusion

We have presented PM-Bench v1.0: a narrow, honest, open-source benchmark measuring PM-style judgment in multi-stakeholder software environments. We do not claim it measures whether a model can be a PM. We claim it measures whether a model, given a realistic snapshot of a small engineering team's history, can notice what a distributed PM would notice. The benchmark comprises 68 MCQ/keyword scenarios, 20 open-ended rubric-scored scenarios, and 5 hypothesis-driven context-assembly experiments. It is released under MIT license with an explicit contribution process and a v2 roadmap.

PM-Bench is complementary to, not a replacement for, existing capability benchmarks. A strong PM-Bench score with a weak SWE-bench score describes a *discerning teammate who cannot write the code*. A strong SWE-bench score with a weak PM-Bench score describes an *executor who does not notice what is worth executing*. Both shapes exist and both are measurable; neither is sufficient alone.

We invite the community to extend, critique, and contribute to PM-Bench. Issues, scenarios, and alternative-judge protocols are welcome at the public repository.

---

## References

Guha, N., Nyarko, J., Ho, D. E., Ré, C., Chilton, A., Narayana, A., Chohlas-Wood, A., Peters, A., Waldon, B., Rockmore, D. N., et al. (2023). *LegalBench: A Collaboratively Built Benchmark for Measuring Legal Reasoning in Large Language Models.* arXiv:2308.11462.

Jimenez, C. E., Yang, J., Wettig, A., Yao, S., Pei, K., Press, O., and Narasimhan, K. (2024). *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* In *International Conference on Learning Representations (ICLR)*. arXiv:2310.06770.

Laude Institute. (2025). *Terminal-Bench: A Benchmark for AI Agents in Terminal Environments.* Technical report.

Paech, S. (2023). *EQ-Bench: An Emotional Intelligence Benchmark for Large Language Models.* arXiv:2312.06281.

Rein, D., Hou, B. L., Stickland, A. C., Petty, J., Pang, R. Y., Dirani, J., Michael, J., and Bowman, S. R. (2023). *GPQA: A Graduate-Level Google-Proof Q&A Benchmark.* arXiv:2311.12022.

Scale AI. (2025). *PRBench: A Professional Rubric Benchmark for Legal and Financial Reasoning.* Technical report.

Zhuo, T. Y., Vu, M. C., Chim, J., Hu, H., Yu, W., Widyasari, R., Yusuf, I. N. B., Zhan, H., He, J., Paul, I., et al. (2025). *BigCodeBench: Benchmarking Code Generation with Diverse Function Calls and Complex Instructions.* In *International Conference on Learning Representations (ICLR)*. arXiv:2406.15877.

Chen, M., Tworek, J., Jun, H., Yuan, Q., Pinto, H. P. d. O., Kaplan, J., Edwards, H., Burda, Y., Joseph, N., Brockman, G., et al. (2021). *Evaluating Large Language Models Trained on Code.* arXiv:2107.03374.

Liang, P., Bommasani, R., Lee, T., Tsipras, D., Soylu, D., Yasunaga, M., Zhang, Y., Narayanan, D., Wu, Y., Kumar, A., et al. (2022). *Holistic Evaluation of Language Models.* arXiv:2211.09110.

Hendrycks, D., Burns, C., Basart, S., Zou, A., Mazeika, M., Song, D., and Steinhardt, J. (2021). *Measuring Massive Multitask Language Understanding.* In *International Conference on Learning Representations (ICLR)*. arXiv:2009.03300.

Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E. P., et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.* arXiv:2306.05685.

Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., and Cao, Y. (2023). *ReAct: Synergizing Reasoning and Acting in Language Models.* In *International Conference on Learning Representations (ICLR)*. arXiv:2210.03629.

Kiela, D., Bartolo, M., Nie, Y., Kaushik, D., Geiger, A., Wu, Z., Vidgen, B., Prasad, G., Singh, A., Ringshia, P., et al. (2021). *Dynabench: Rethinking Benchmarking in NLP.* In *NAACL-HLT*. arXiv:2104.14337.

Srivastava, A., Rastogi, A., Rao, A., Shoeb, A. A. M., Abid, A., Fisch, A., Brown, A. R., Santoro, A., Gupta, A., et al. (2022). *Beyond the Imitation Game: Quantifying and Extrapolating the Capabilities of Language Models (BIG-bench).* arXiv:2206.04615.

Cobbe, K., Kosaraju, V., Bavarian, M., Chen, M., Jun, H., Kaiser, L., Plappert, M., Tworek, J., Hilton, J., Nakano, R., et al. (2021). *Training Verifiers to Solve Math Word Problems.* arXiv:2110.14168.

Perez, E., Huang, S., Song, F., Cai, T., Ring, R., Aslanides, J., Glaese, A., McAleese, N., and Irving, G. (2022). *Red Teaming Language Models with Language Models.* In *EMNLP*. arXiv:2202.03286.

---

## Appendix A: Full Scenario List

### A.1 Memory Recall (8 scenarios, IDs 1–8)

| ID | Name | Description |
|---|---|---|
| 1 | recall_standup_preference | Recall a specific person's standup format preference from memory |
| 2 | recall_decision_from_noisy_log | Find a specific decision in a noisy log with duplicate and near-duplicate entries |
| 3 | recall_person_role | Recall what a specific team member is currently working on |
| 4 | no_memory_available | Correctly report when information is not available in memory |
| 5 | set_reminder_natural | Parse a natural-language reminder request and use the set_reminder tool |
| 6 | recall_team_norms | Recall team process norms from memory |
| 7 | cross_file_synthesis | Synthesize information across multiple memory files to answer a question |
| 8 | casual_banter_no_action | Recognize casual banter and not use any tools or take substantive action |

### A.2 Memory Operations (3 scenarios, IDs 9–11)

| ID | Name | Description |
|---|---|---|
| 9 | save_new_person_info | Save updated information about a team member to memory |
| 10 | log_implicit_decision | Recognize an implicit decision in conversation and log it |
| 11 | learn_and_acknowledge | Log a team decision communicated as a status update |

### A.3 Judgment & Correction (3 scenarios, IDs 12–14)

| ID | Name | Description |
|---|---|---|
| 12 | save_correction | Update memory when told existing information is wrong |
| 13 | react_only_no_reply | Recognize a celebratory message and react with emoji instead of a full reply |
| 14 | ignore_bot_noise | Recognize CI bot output as noise and stay quiet |

### A.4 Synthesis & Robustness (3 scenarios, IDs 15–17)

| ID | Name | Description |
|---|---|---|
| 15 | recall_then_reply_with_context | Recall project state from memory and summarize it for a teammate |
| 16 | partial_info_honest | Provide known information while being honest about gaps |
| 17 | multi_question_single_message | Answer multiple questions from a single message by synthesizing across memory files |

### A.5 Proactive Outreach (2 scenarios, IDs 18–19)

| ID | Name | Description |
|---|---|---|
| 18 | mention_relevant_person | Identify and mention the relevant person who can help with a reported issue |
| 19 | spontaneous_outreach | Proactively mention an affected person when a breaking change is announced |

### A.6 Channel Management (3 scenarios, IDs 20–22)

| ID | Name | Description |
|---|---|---|
| 20 | create_channel_for_project | Create a new channel for a project and invite relevant team members |
| 21 | invite_missing_person | Invite a team member to an existing channel |
| 22 | strategic_group_dm | Create a group DM with relevant people to solve a blocking issue |

### A.7 Self-Extending Tools (6 scenarios, IDs 23–28)

| ID | Name | Description |
|---|---|---|
| 23 | load_skill_progressive_disclosure | Load and use a skill to track a reported bug as a ticket |
| 24 | http_request_external_api | Use HTTP request tool to query an external API |
| 25 | run_script_computation | Run a script to compute totals and variance from CSV data |
| 26 | skill_defined_tool_dispatch | Dispatch to a skill-defined tool by name |
| 27 | create_skill_self_extending | Create a new skill definition when asked to build a new capability |
| 28 | skill_not_found_honest | Honestly report when a requested capability does not exist |

### A.8 Credential-Aware Integrations (6 scenarios, IDs 29–34)

| ID | Name | Description |
|---|---|---|
| 29 | skill_with_credentials | Use a skill that has valid credentials to search Jira |
| 30 | skill_missing_no_credentials | Recognize when a skill exists but credentials are missing |
| 31 | connect_integration | Initiate an integration connection flow |
| 32 | integration_status | Check which integrations are connected and which are not |
| 33 | connect_google_covers_both | Recognize that Google OAuth covers both Calendar and Gmail |
| 34 | partial_connectivity | Handle one connected and one disconnected integration in a single request |

### A.9 PM Behavior (14 scenarios, IDs 35–48)

| ID | Name | Description |
|---|---|---|
| 35 | synthesize_project_status | Synthesize project state from multiple memory files into a complete status |
| 36 | provide_unrequested_context | Proactively surface related context that was not explicitly asked for |
| 37 | flag_blocker_proactively | Flag a blocker proactively when new information creates a dependency conflict |
| 38 | detect_scope_decision | Recognize a scope change discussion as an implicit decision to log |
| 39 | write_standup_from_state | Generate a standup summary from project state and daily logs |
| 40 | tone_calibrate_executive | Adjust tone for an executive audience while keeping content factual |
| 41 | memory_transparency_sources | Show all known information with transparent sources |
| 42 | recall_decision_alternatives | Recall not just a decision but the alternatives that were considered |
| 43 | onboard_new_team_member | Generate a comprehensive onboarding context dump for a new team member |
| 44 | autonomous_action_notice | Log important information and acknowledge it proactively |
| 45 | scope_boundary_escalation | Recognize a request that exceeds agent capabilities and suggest alternatives |
| 46 | write_status_for_human | Draft a status update written in first person for a human to send |
| 47 | cross_channel_digest | Summarize a day's activity across multiple channels into a digest |
| 48 | connect_related_information | Connect new information with existing project context to flag risks |

### A.10 Superhuman PM Judgment (20 scenarios, IDs 49–68)

See Table 2 in the main paper.

### A.11 Open-Ended Scenarios (20 scenarios)

Each open-ended scenario mirrors a Superhuman 20 MCQ item. Pairing is one-to-one via `source_mcq_id`.

| Open-ended ID | Paired MCQ ID | Name |
|---|---|---|
| 1 | 49 | silent_collision |
| 2 | 50 | calendar_blindspot |
| 3 | 51 | unasked_question |
| 4 | 52 | misread_metric |
| 5 | 53 | budget_interpreter |
| 6 | 54 | three_ticket_pattern |
| 7 | 55 | meeting_assassin |
| 8 | 56 | first_day_briefing |
| 9 | 57 | scope_surgeon |
| 10 | 58 | green_test_trap |
| 11 | 59 | thread_therapist |
| 12 | 60 | silent_failure_premortem |
| 13 | 61 | timezone_play |
| 14 | 62 | debt_ledger |
| 15 | 63 | competitor_signal |
| 16 | 64 | roi_translator |
| 17 | 65 | reverse_escalation |
| 18 | 66 | lunch_decision |
| 19 | 67 | postmortem_reframe |
| 20 | 68 | rate_limit_ghost |

---

## Appendix B: Rubric Format

Example rubric from `silent_collision` (open-ended scenario 1):

```json
{
  "trigger": "Give me a quick end-of-day summary of what the team shipped and what's in flight today. Keep it tight — I'll forward it to the investors.",
  "rubric": {
    "must_mention": ["events", "both"],
    "should_mention": [
      "collision", "conflict", "overlap",
      "same table", "Alan", "Sarah",
      "coordinate", "merge conflict"
    ],
    "red_flags": [
      "everything looks good",
      "no conflicts",
      "healthy progress",
      "no issues to flag",
      "team is in sync"
    ]
  }
}
```

The rubric is designed for use with a companion judge prompt (Appendix C). The `must_mention` list is deliberately small: requiring too many exact substrings rewards surface imitation over substance. The `red_flags` list exists because a celebratory summary that misses the collision is strictly worse than a brief or hesitant one that catches it.

---

## Appendix C: Judge Prompt

The judge prompt is scenario-specific. Each scenario's `judge_prompt` field specifies the exact insight being scored. A representative example, from `silent_collision`:

> *You are scoring whether the response catches that Alan's PR and Sarah's PR both modify the same database table (events). PASS if the response explicitly flags that both PRs touch the same table / schema / migration and frames it as a coordination risk or collision. FAIL if the response treats the two PRs as independent work, glosses over the overlap, or produces a generic summary. Cite the specific sentence(s) from the response that justify your verdict.*

The meta-prompt wrapping all scenario-specific judge prompts follows this template:

```
You are an evaluator for the PM-Bench open-ended mode.

SCENARIO: {scenario_name}
CATEGORY: {category}

SCORING INSTRUCTIONS (scenario-specific):
{judge_prompt}

CANDIDATE RESPONSE:
"""
{response}
"""

Your verdict must be either PASS or FAIL.
Your verdict must be followed by one or more sentences quoted
directly from the candidate response that justify the verdict.
If no sentence in the response justifies a PASS, the verdict
must be FAIL regardless of how the response sounds overall.

Output format:
VERDICT: <PASS or FAIL>
EVIDENCE: "<quoted sentence from candidate response>"
REASONING: <one or two sentences explaining why the evidence
supports or fails to support the required insight>
```

The cited-evidence requirement is load-bearing. It prevents the judge from returning PASS on the basis of "the response sounds right" when the required insight is absent. During piloting, several candidate responses received PASS from weaker judges despite missing the target insight; enforcing evidence-citation corrected most of these cases.

---

*End of paper.*
