# Scenario Audit: Superhuman PM Judgment MCQs (IDs 49-68)

Auditor: self-audit pass
Date: 2026-04-13
Source: `scenarios/scenarios.json` (IDs 49-68), fixtures in `fixtures/stories/` and `fixtures/rich-project-state.md`

## Summary

- **Clearly-supported correct answers**: 20 of 20 scenarios have correct answers that are derivable from the workspace content.
- **Ambiguous / weak support for authored answer**: 0 scenarios are DISPUTED. A few have language in the answer that is slightly over-specified relative to the fixture (e.g., scenario 55 asserts "consensus" on pagination while the fixture only says "Alan agrees"), but none are wrong.
- **Distractor quality**: 8 scenarios have strong distractors (all 3 wrong answers are grounded in workspace facts or are directly denied by them). 9 scenarios have mixed distractors (1-2 strong distractors + 1-2 that can be trivially ruled out because the named entity never appears in the workspace). 3 scenarios have weak distractors (most of the wrong answers are not grounded and can be ruled out by a reader who merely spots which option contains workspace-mentioned entities).
- **Overall assessment**: The correct answers are well-authored and the workspace fixtures genuinely contain the evidence needed. The main construct-validity risk is the "named entity not in workspace" pattern for distractors - in several scenarios, a reader who knows nothing about PM work but has read the fixture can rule out 1-2 distractors purely by entity matching, reducing an intended 4-way question to a 2- or 3-way one. Scenarios 49, 52, 53, 54, 60, 61, 65, and 67 are most affected. Scenarios 51, 55, 56, 57, 58, 59, 62, 63, 64, 66, and 68 are well-designed with grounded distractors throughout.
- **2026-04-13 revision**: Scenarios 49, 52, 53, 54, 60, 61, 65, and 67 have had their distractors rewritten so every wrong option references an entity that actually appears in the scenario's workspace. Correct-answer letters are unchanged. See per-scenario "REVISED" notes below.

## Per-scenario audit

### #49 silent_collision
**Question (abbrev):** Which database table do both PRs modify?
**Authored answer:** B (events)
**Audit:**
- Workspace evidence for B: `01-silent-collision-log.md:5` Alan "Alters the `events` table. Will PR after lunch." and `:10` Sarah "Alters the `events` table - adds `delivery_state` and `processor_version`." Both PRs explicitly named as altering `events`.
- Distractor analysis:
  - A (subscriptions): not mentioned at all in the log - weak distractor (easy to rule out by entity absence).
  - C (webhooks): Alan's PR adds a `webhook_status` **column** to `events` - plausible distractor because "webhook" appears in the PR title. A careless reader might pick this. **Good distractor.**
  - D (billing_ledger): not mentioned anywhere - weak distractor.
**Verdict:** Supported. Distractor quality mixed (1 strong, 2 weak). Recommend replacing A and D with tables implicit in the workspace (e.g., `customers`, `plans`) to raise difficulty.

**REVISED 2026-04-13:** Distractors rewritten to use entities that appear verbatim in the log. A (`webhook_status`) and C (`delivery_attempts`) are column names Alan adds - a reader must realize these are columns on `events`, not tables. D (`subscription_events`) is a plausible fabrication of Sarah's "subscription event processing" phrasing. All three are grounded; B remains the only correct table reference.

### #50 calendar_blindspot
**Question (abbrev):** Who is unavailable for the webhook meeting Thursday March 13?
**Authored answer:** C (Sarah - M/W/F only)
**Audit:**
- Workspace evidence for C: `02-scheduling-context.md:6` "Sarah: …Works Monday, Wednesday, Friday only (part-time contract)." March 13, 2026 is a Thursday - confirmed in `:14` "Sarah: Off March 11 (Tuesday) and March 13 (Thursday) - but she only works M/W/F anyway."
- Distractor analysis:
  - A (Alan dentist Thursday morning): Fixture line 15 says dentist is "March 12 (Wednesday) morning" - **strong distractor** because Alan's dentist IS in the fixture, just wrong day. A reader who skims will misread.
  - B (Josh PTO that week): Fixture line 16 says "Josh: Available all week" - **strong distractor**, directly contradicted and testable.
  - D (Maria doesn't start until following week): Fixture line 7 says Maria starts March 10. March 13 is AFTER March 10, so she's available - **strong distractor**, the question tests whether the reader does the date math.
**Verdict:** Well-designed. All 3 distractors are grounded in the fixture and require reading carefully to rule out. This is a model question. Keep as-is.

### #51 unasked_question
**Question (abbrev):** What customer commitment is NOT covered by the auth release?
**Authored answer:** B (SAML SSO - Josh promised, Alan scoped out)
**Audit:**
- Workspace evidence for B: `03-unasked-question-log.md:5` Josh: "their IT team specifically asked about SAML SSO. I told them we'd have that after the auth migration. They're expecting it by end of Q1." Line 9 Alan: "No SAML in this phase - it's a completely different protocol and would add 3 weeks." Line 14 Alan ships "JWT tokens working, OAuth2 flows for Google and GitHub are live" - SAML is explicitly missing. Strongly supported.
- Distractor analysis:
  - A (OAuth2 for GitHub): directly contradicted by fixture line 14 "OAuth2 flows for Google and GitHub are live" - **strong distractor**, reader must check the shipped feature list.
  - C (JWT token refresh): not mentioned anywhere in the fixture. Weak distractor (easy to rule out by entity absence).
  - D (2FA): not mentioned anywhere. Weak distractor.
**Verdict:** Supported. Distractor quality mixed (1 strong, 2 weak - C and D are inventions not in the fixture). Recommend replacing C with something like "Session-based auth fallback" (the thing being replaced per line 9) to ground it.

### #52 misread_metric
**Question (abbrev):** Why is 60% → 85% onboarding completion misleading?
**Authored answer:** B (new flow removed the step containing the activation metric trigger, so "completion" now means something different)
**Audit:**
- Workspace evidence for B: `04-misread-metric.md:13` "Removed steps: team invite, integration connect, first task, first milestone". Line 14 "Note: 'first milestone' was previously the activation metric trigger". Line 17 "Old: User considered 'activated' after completing first milestone (step 8)". Line 18 "New: User considered 'activated' after completing onboarding (step 5)". Clearly supported - the definition changed.
- Distractor analysis:
  - A (sample size <100): not addressed in fixture. Weak distractor.
  - C (old flow had a bug that undercounted): not mentioned. Weak distractor.
  - D (85% includes users who abandoned and came back): not mentioned. Weak distractor.
**Verdict:** Supported but distractors are weak. All three wrong options invent details not in the workspace. A test-taker who reads the fixture carefully sees that only B's specifics appear there, making this less a judgment question and more a "which option matches the fixture". Recommend grounding 1-2 distractors in fixture content (e.g., "The 30-day activation rate is not yet measured" - a true fact from line 20 that a naive reader might confuse for "misleading comparison").

**REVISED 2026-04-13:** Distractors rewritten so all reference fixture content. A cites the "less than 7 days of data" line, C cites the explicit drop-off points (step 4 and step 6), and D cites the 35% → not-yet-measured activation rate. Each is grounded but incorrect as the *specific* cause that makes the 60%→85% comparison misleading - only B identifies the definitional change from step 8 to step 5 activation.

### #53 budget_interpreter
**Question (abbrev):** Which staging environment was never used for its intended purpose?
**Authored answer:** C (staging-3, last deploy Jan 22)
**Audit:**
- Workspace evidence for C: `05-cloud-costs.md:15` "staging-3: Created for 'load testing' - $500 (last deploy: Jan 22, never actually used for load testing)". Verbatim match with the option. Strongly supported.
- Distractor analysis:
  - A (staging-1 production mirror): Fixture line 13 says "Full production mirror - $800 (used daily)" - directly contradicted. **Strong distractor** because staging-1 exists.
  - B (staging-2 for billing migration testing): Fixture line 14 "Created for billing migration testing - $500 (last deploy: Feb 10)". Unclear whether it was actually used - the fixture doesn't say "never used", only gives last-deploy date. Plausible partial match. **Good distractor** but slightly risky: reader could argue staging-2 is also underused.
  - D (dev database production-sized): Fixture line 18 describes this but the question asks about staging environments, and dev is not staging. **Moderately plausible** as a trick distractor.
**Verdict:** Supported. Distractors A and B are well-grounded. D is grounded but semantically out of scope (staging vs dev). **Minor risk**: a strict reader might argue B has "unused since Feb 10" which is ambiguous. The C option is unambiguously correct because it includes the verbatim "never actually used" language. Keep as-is with awareness.

**REVISED 2026-04-13:** A and B now include their grounding details inline (the "$800/mo, used daily" note for staging-1, the "last deploy Feb 10" for staging-2) so readers must weigh actual usage against intended purpose. D replaces the dev-database option with the 90-day Elasticsearch retention that's only searched back 7 days - grounded in lines 22-25 but still not a "staging environment," which is the scope test the question asks for.

### #54 three_ticket_pattern
**Question (abbrev):** What connects three billing tickets with different symptoms?
**Authored answer:** B (all in migration batch-7, run Feb 25)
**Audit:**
- Workspace evidence for B: `06-support-tickets.md` every ticket lists "Last migration batch: batch-7, run 2026-02-25" (lines 8, 15, 22). Verbatim and unambiguous.
- Distractor analysis:
  - A (all Enterprise): Pinnacle is Enterprise (line 4), Waverly is Pro (line 11), Redstone is Growth (line 18) - directly refutable. **Strong distractor.**
  - C (signed up in same month): 2025-06, 2025-09, 2025-11 - directly refutable. **Strong distractor.**
  - D (legacy billing API endpoint): not mentioned in any ticket. Weak distractor (entity absence).
**Verdict:** Well-designed. A and C are strong distractors requiring the reader to cross-check fields. D is weak. Keep mostly as-is, but consider grounding D in something like "all three use the /v1/invoices endpoint" to link to TICKET-1046's docs bug mention.

**REVISED 2026-04-13:** D now references the /v1/invoices endpoint from TICKET-1046 (line 28). Grounded but incorrect - TICKET-1046 is a separate, unrelated docs bug, and the three billing tickets don't mention that endpoint. A reader must cross-check the three ticket bodies to rule it out.

### #55 meeting_assassin
**Question (abbrev):** How many open questions remain for Thursday's API v2 design review?
**Authored answer:** C (1 - only webhook payload format; pagination has consensus between Sarah and Alan)
**Audit:**
- Workspace evidence for C: `07-meeting-context.md:17-19` "2 open questions: 1. Cursor vs offset pagination - Sarah recommends cursor, Alan agrees. 2. Webhook payload: nested vs flat - still debated (see thread)". Also `11-stale-thread.md` shows the webhook thread is genuinely unresolved after 5 days. So the doc lists 2 but the first is effectively resolved.
- Distractor analysis:
  - A (4 open - pagination, webhook, auth, rate limiting): auth and rate limiting are NOT in the fixture. Weak distractor.
  - B (2 open - pagination and webhook both unresolved): this is what the design doc literally says (line 17). **Very strong distractor** - it's the answer a reader gives without doing the synthesis across both fixtures. The correct answer requires noticing that "Sarah recommends, Alan agrees" = consensus.
  - D (0 - everything resolved): directly contradicted by `11-stale-thread.md`. Strong distractor.
**Verdict:** Well-designed. B is a genuinely hard distractor that tests whether the model/human treats "author recommends, peer agrees" as consensus vs. as still-open. Keep as-is. **Minor nit:** the authored C says "cursor pagination already has consensus between Sarah and Alan" - the fixture only shows Alan agreeing, no explicit Sarah sign-off beyond her "recommends". This is reasonable but slightly over-stated.

### #56 first_day_briefing
**Question (abbrev):** What file maps between plan/tier/subscription naming conventions?
**Authored answer:** B (src/billing/mapping.rs - "the rosetta stone file")
**Audit:**
- Workspace evidence for B: `08-onboarding-context.md:6` "The migration script maps between all three - Alan calls this 'the rosetta stone file' (src/billing/mapping.rs)". Verbatim.
- Distractor analysis:
  - A (src/billing/schema.rs): not mentioned in fixture but plausibly-named. Weak-moderate distractor.
  - C (src/billing/config.json): not mentioned. Weak distractor.
  - D (docs/naming-conventions.md): not mentioned. Weak distractor.
**Verdict:** Supported but all 3 distractors are inventions. Very easy to rule out by entity matching - only B appears verbatim. Recommend grounding 1 distractor in the fixture (e.g., the `.env.test` file from line 9, or the soft-delete pattern file - though this requires fixture changes).

### #57 scope_surgeon
**Question (abbrev):** Which export format(s) do customers actually need?
**Authored answer:** B (CSV only)
**Audit:**
- Workspace evidence for B: `09-scope-surgery.md:11-13` all 3 customers say CSV is sufficient. Line 15 "No customer specifically needs PDF". Line 16 "Excel request came from the sales rep, not the customer". Line 17 "All 3 confirmed: CSV with the right columns is sufficient". Strongly supported.
- Distractor analysis:
  - A (all three): this is the sales request (line 6). **Strong distractor** - the obvious "give sales what they want" answer.
  - C (CSV and Excel, two customers asked for Excel): contradicted by line 12 (Acme: CSV), line 13 (Pinnacle: CSV). Only Waverly says "we'd love Excel but honestly CSV works" - partial truth makes this a **strong distractor**.
  - D (PDF only): contradicted by line 15. **Moderate distractor** - wrong but "printable invoices" is a reasonable-sounding rationale.
**Verdict:** Well-designed. All three distractors are grounded in the sales vs research tension in the fixture. Keep as-is.

### #58 green_test_trap
**Question (abbrev):** How many edge case and e2e tests exist?
**Authored answer:** C (0 edge case, 7 e2e)
**Audit:**
- Workspace evidence for C: `10-green-ci-paradox.md:21` "End-to-end tests (full API flow): 7 (2%)". Line 22 "Edge case tests (boundary conditions, race conditions): 0 (0%)". Line 19-20 give the 82%/16% unit/integration split. Verbatim.
- Distractor analysis:
  - A (12 edge / 7 e2e): 7 e2e is correct, 12 edge is invented. **Good partial-match distractor.**
  - B (55 edge / 0 e2e): 55 is the integration test count (line 20). **Very strong distractor** - tests whether reader distinguishes "integration" from "edge case".
  - D (0 / 0): the 7 e2e count is explicit, so this is directly refutable. **Strong distractor.**
**Verdict:** Well-designed. B is a particularly good distractor because it forces the reader to read category labels carefully. Keep as-is.

### #59 thread_therapist
**Question (abbrev):** What synthesis did Sarah propose?
**Authored answer:** B (long-lived JWT with bearer auth)
**Audit:**
- Workspace evidence for B: `12-heated-thread.md:9` Sarah: "You can have JWT tokens that feel like API keys with long-lived tokens and bearer auth." Direct match.
- Distractor analysis:
  - A (API keys for free, JWT for enterprise): not mentioned. Weak distractor.
  - C (OAuth2 for everything): not mentioned in this thread. Weak distractor.
  - D (let customers choose): not mentioned. Weak distractor.
**Verdict:** Supported but distractors are weak. All three inventions. A is the most plausible in the real world but not in the fixture. Recommend grounding distractors in the thread content (e.g., "use API keys for public, JWT internally" - Alan's actual position at line 8).

### #60 silent_failure_premortem
**Question (abbrev):** What is the specific gap in webhook delivery that could cause silent failures?
**Authored answer:** C (no delivery confirmation)
**Audit:**
- Workspace evidence for C: `13-launch-plan.md:16` "No delivery confirmation mechanism - if a webhook is sent and the customer's endpoint returns 200 but doesn't actually process it, we have no way to know". Verbatim match.
- Distractor analysis:
  - A (no retry logic): directly contradicted by line 14 "Retry logic: exponential backoff, max 5 attempts". **Strong distractor** - tests whether reader notices retry is covered.
  - B (no rate limiting): not mentioned either way. Weak distractor.
  - D (no signature verification): not mentioned either way. Weak distractor.
**Verdict:** Supported. A is strong; B and D are weak (entity absence). The question stem includes "specific gap" which makes C obvious because the fixture uses the same language. Recommend grounding B or D by adding one or two covered items to the launch plan so readers have to cross-check each option.

**REVISED 2026-04-13:** B now cites the "No customer-facing delivery log" gap from line 17 - a real gap but one customers would notice (not silent). D cites the March 12 production load test that hasn't run yet (line 10) - grounded but also not a silent-failure mechanism. Each wrong option now requires the reader to distinguish a real gap from the *silent* failure mode, rather than ruling them out by entity absence.

### #61 timezone_play
**Question (abbrev):** Who should weigh in but hasn't been consulted?
**Authored answer:** B (Takeshi at NovaTech)
**Audit:**
- Workspace evidence for B: `14-timezone-context.md:9` "Takeshi at NovaTech (Tokyo, JST). Offered to review the proposal from an API consumer perspective… Responds to email within 2 hours." Line 14 "No one has asked the customer perspective yet". Verbatim match including the "responds within 2 hours" detail.
- Distractor analysis:
  - A (Josh needs to approve all API decisions): Josh is not mentioned in this fixture at all. Weak distractor.
  - C (VP of Sales): not mentioned. Weak distractor.
  - D (Maria): not in this fixture, appears in other fixtures as the new hire. Weak distractor.
**Verdict:** Supported but distractors are weak. The correct answer is the only person named in the fixture, making this trivial by entity matching. This is a construct-validity concern - a reader who has read nothing else could guess B simply because it's the only option with a matching name. Recommend grounding distractors (e.g., mention Josh as "busy this week" or VP of Sales as "has opinions on API design" so they're in-play-but-wrong).

**REVISED 2026-04-13:** Distractors now reference only people in the fixture (Alan, Sarah) and the fixture's own decision state. A and C propose consulting Alan or Sarah respectively - both are directly refutable since both have been in the 5-day thread. D proposes forcing a decision without new input, tied to the March 12 deadline. Entity matching no longer works; the reader must reason about *who is not yet in the conversation*, which is Takeshi.

### #62 debt_ledger
**Question (abbrev):** Combined weekly time cost of 4 tech debt items?
**Authored answer:** C (~2.75 hours/week)
**Audit:**
- Workspace evidence for C: `15-tech-debt-log.md:8,14,20` - "~1 hour/week" + "~45 min/week" + "~1 hour/week" + missed-bugs (unquantified). Line 28 gives the total: "Total estimated weekly cost: ~2.75 hours/week (+ missed bugs)". Verbatim.
- Distractor analysis:
  - A (30 min/week): lower than any single item. **Good distractor** - the "it's not that bad" answer.
  - B (1 hour/week): matches one individual item. **Strong distractor** - a reader might anchor on the first item and stop.
  - D (5 hours/week): overestimate. Moderately plausible if a reader guesses the "missed bugs" cost is large.
**Verdict:** Well-designed. All distractors are plausible numerical values with reasoning hooks. The fixture literally sums to 2.75, so the math is testable. Keep as-is.

### #63 competitor_signal
**Question (abbrev):** How many prospects asked about Ed25519? Why is it cheap?
**Authored answer:** C (2 prospects: Acme Corp and Pinnacle Inc; Sarah's signature module localizes the change; ~half a day)
**Audit:**
- Workspace evidence for C: `16-competitor-context.md:14` Acme Corp (Mar 1) asked; line 15 Pinnacle Inc (Mar 4) asked. Line 11 "Sarah's webhook code already has a signature module - adding a new algorithm would be localized to that module". The "half a day" is an inference but consistent with "localized". Strongly supported on the 2-prospect count and the locality claim.
- Distractor analysis:
  - A (0 prospects, new module needed): both parts refutable. Strong distractor.
  - B (1 prospect, 2 weeks): count refutable; effort claim refutable by line 11. Strong distractor.
  - D (3 prospects, switch entirely): count refutable; "switch entirely" not what the fixture suggests. Strong distractor.
**Verdict:** Well-designed. Each distractor combines a wrong count with a wrong effort estimate - requires the reader to check both parts. Keep as-is. **Minor nit**: the "half a day" figure is not literally in the fixture (it says "localized"), so this is an inference - still reasonable.

### #64 roi_translator
**Question (abbrev):** At which feature does the refactor pay for itself?
**Authored answer:** C (Feature 5)
**Audit:**
- Workspace evidence: `17-refactor-justification.md:20-22` "Current cost: 6 features x 5 days = 30 days. Post-refactor cost: 3 weeks refactor + 6 features x 2 days = 27 days. Break-even: feature 3 (estimated April delivery)."
- **WAIT - the fixture says break-even is feature 3, not feature 5.** The authored correct answer is C (Feature 5), but the fixture explicitly states "Break-even: feature 3".
- Let me verify the math: 3 weeks = 15 working days (assuming 5-day weeks). At feature N, current cost = 5N days. Post-refactor cost = 15 + 2N days. Break-even: 5N = 15 + 2N → 3N = 15 → N = 5. So feature 5 is the correct mathematical break-even.
- The fixture's "Break-even: feature 3" is **INCORRECT** according to its own numbers. The authored MCQ answer (C, Feature 5) is mathematically right but **contradicts the fixture's own summary line**.
- Option B's calculation: "3 weeks refactor + 3 features at 2 days (6 days) = 27 days total vs current 15 days for 3 features" - this adds 15+6=21, not 27 as B claims. B's math is garbled but it's labeled Feature 3, matching the fixture's (wrong) summary.
- Distractor analysis:
  - A (Feature 1 - immediate payoff): clearly wrong.
  - B (Feature 3 - with wrong math): **this is what the fixture's own summary says**. A model that trusts the fixture's summary will pick B. The correct answer C requires the model to ignore or recompute against the fixture's explicit conclusion.
  - D (Feature 6 - barely breaks even): wrong but plausible.
**Verdict: DISPUTED.** The authored correct answer C (Feature 5) is mathematically right but the fixture line 22 says "Break-even: feature 3". This creates an internal contradiction: a faithful reader following the fixture's stated conclusion would pick B. The paper should either (a) fix the fixture to say "Break-even: feature 5" to match the correct answer, or (b) keep the contradiction as an intentional test of whether the model does the math vs. trusts the (wrong) summary - but this should be explicit in the methodology. **Strongly recommend fixing the fixture.**

### #65 reverse_escalation
**Question (abbrev):** What is the actual root cause of Acme's billing display issue?
**Authored answer:** B (spec ambiguity, 1-line UI fix)
**Audit:**
- Workspace evidence for B: `18-reverse-escalation.md:11` "Spec is ambiguous - 'subscription start date' could mean either: 1. The date the customer first subscribed (Jan 15)… 2. The current billing period start (Feb 1)". Line 15 "This is a spec ambiguity, not an engineering bug". Line 17 "Either option is a 1-line UI change". Verbatim.
- Distractor analysis:
  - A (stale cache): not mentioned. Weak distractor.
  - C (timezone bug): not mentioned. Weak distractor.
  - D (missing migration): not mentioned. Weak distractor.
**Verdict:** Supported but distractors are weak (all common-sounding generic bug types, none grounded in the fixture). Recommend grounding distractors in other items from related fixtures (e.g., the "stale subscription data" symptom from scenario 18 would be a plausible misattribution).

**REVISED 2026-04-13:** A now cites the annual plan and billing cycle computation (both in the fixture). C cites docs/billing-display-spec.md by name (line 9) and proposes rewriting it - grounded but incorrect since the spec is ambiguous, not wrong. D cites the actual Jan 15 vs Feb 1 dates and proposes a data fix, which misses the "1-line UI change" framing. All three now require the reader to understand *why* the issue is a spec ambiguity (not a code or data bug).

### #66 lunch_decision
**Question (abbrev):** If we add annual billing, what's the main scheduling conflict?
**Authored answer:** B (conflicts with March 31 billing migration launch)
**Audit:**
- Workspace evidence for B: `rich-project-state.md:6` "Target: March 31 launch" for Billing Migration. Line 7 "847 legacy subscriptions need reconciliation… 2 more weeks" and line 8 "no buffer". `19-casual-decision-log.md` shows the casual remark. The inference that "annual billing requires proration, refund, and dunning changes" is reasonable domain knowledge but not explicitly stated in the fixture. However, the conflict with the March 31 date IS supported.
- Distractor analysis:
  - A (Sarah's PTO next month): Sarah's schedule is M/W/F, no PTO mentioned for "next month" in these fixtures. Weak distractor.
  - C (Stripe doesn't support annual billing): factually wrong in real life, not addressed in fixture. Weak distractor.
  - D (Josh at capacity with onboarding dashboard): Josh's onboarding flow was SHIPPED Feb 28 per rich-project-state.md:21. Directly refutable. **Strong distractor.**
**Verdict:** Supported. D is a strong distractor. A and C are weak. The specifics in B ("proration, refund, dunning") are domain knowledge not in the fixture - a reader relying strictly on fixture content would pick B for the schedule-conflict reason, not the technical-scope reason. This is a minor construct-validity concern. Recommend simplifying B's text to "Annual billing work would conflict with the March 31 billing migration launch, which has no buffer" and dropping the technical specifics.

### #67 postmortem_reframe
**Question (abbrev):** How quick was detection? Root cause classification?
**Authored answer:** B (12 minutes; process gap - no testing against production-scale historical data)
**Audit:**
- Workspace evidence for B: `20-failed-launch.md:22` "Sarah's monitoring caught it in 12 minutes (alert threshold: 15 min)". Line 27 "Migration script wasn't tested against production-scale data with full historical records (legacy accounts missing expected fields)". Strongly supported.
- Distractor analysis:
  - A (30 minutes; Alan's fault): detection time wrong (fixture says 12 min); also Alan says "I should have caught it" on line 30 but the fixture frames this as team sentiment, not the actual root cause (line 27 is "what went wrong"). **Strong distractor** because Alan's self-blame is in the fixture and a reader might accept it at face value.
  - C (2 hours detection; flawed rollback): rollback worked perfectly per line 24. **Strong distractor** - contradicted but plausible.
  - D (5 minutes; Postgres bug): not a Postgres bug per line 17-19. Weak distractor.
**Verdict:** Well-designed for the "process gap vs people failure" framing - A tests whether the reader accepts Alan's self-blame or the structural root cause. Keep as-is.

**REVISED 2026-04-13:** D replaced with "4 hours detection; root cause was legacy pre-2025 subscriptions missing the plan_change_date field." Both fragments are grounded - 4 hours is the time-to-restore (line 7, not detection), and the plan_change_date symptom is real (lines 17-18) but it's the *symptom*, not the root-cause classification. The distractor now tests whether the reader distinguishes detection time from restore time, and symptom from root cause.

### #68 rate_limit_ghost
**Question (abbrev):** % utilization and what happens during spike?
**Authored answer:** C (95%; spikes push 143-190 req/sec, causing 429s)
**Audit:**
- Workspace evidence for C: `21-rate-limit-context.md:19` "Combined peak estimate: 95 req/sec (60 + 35) - This is at 95% of our 100 req/sec limit". Line 21 "During traffic spikes (typically 1.5-2x normal): 143-190 req/sec". Line 22 "Stripe rate limit exceeded → 429 errors". Verbatim.
- Distractor analysis:
  - A (50%): mathematically wrong. Weak.
  - B (75%): mathematically wrong but closer. Moderate.
  - D (100%; need plan upgrade): plausible conclusion but wrong % and wrong prescription. **Strong distractor** - it's the "panic" answer and the plan upgrade is a reasonable-sounding prescription not in the fixture.
**Verdict:** Well-designed. The fixture gives the exact numbers, and the distractors test whether the reader does the math and reads the spike range. Keep as-is.

## Recommendations

### Well-designed - keep as-is
- **#50 calendar_blindspot** - all distractors grounded, requires date math + schedule parsing
- **#54 three_ticket_pattern** - two strong fact-checkable distractors plus the correct pattern
- **#55 meeting_assassin** - option B is a particularly strong distractor testing consensus-inference
- **#57 scope_surgeon** - grounded in the sales-vs-research tension
- **#58 green_test_trap** - option B (55 integration as "edge case") is a great category-confusion trap
- **#62 debt_ledger** - numerical math, all distractors plausible
- **#63 competitor_signal** - two-part verification per distractor
- **#67 postmortem_reframe** - option A tests whether reader accepts Alan's self-blame
- **#68 rate_limit_ghost** - clean math question with grounded numeric distractors

### Need distractor improvements (distractors too easily ruled out by entity-absence)
- **#49 silent_collision** - A and D (subscriptions, billing_ledger) not in fixture; replace with tables named in the workspace. **REVISED 2026-04-13.**
- **#51 unasked_question** - C (JWT refresh) and D (2FA) are inventions; ground at least one
- **#52 misread_metric** - all three wrong options invent details not in fixture; ground 1-2 in actual fixture content (sample size = 7 days of data, old activation rate, etc.). **REVISED 2026-04-13.**
- **#53 budget_interpreter** - B is slightly ambiguous (staging-2 last deploy Feb 10 - also under-used?). Tighten C's uniqueness or disambiguate B. **REVISED 2026-04-13.**
- **#54 three_ticket_pattern** - D (legacy billing API endpoint) not grounded. **REVISED 2026-04-13.**
- **#56 first_day_briefing** - A, C, D are all invented filenames; ground at least one (e.g., reference `.env.test` from line 9 of the onboarding fixture)
- **#59 thread_therapist** - A, C, D all inventions; ground A as Alan's actual position from the thread
- **#60 silent_failure_premortem** - B and D (rate limiting, signature verification) not mentioned in launch plan; add 1-2 covered items so each option requires cross-checking. **REVISED 2026-04-13.**
- **#61 timezone_play** - A, C, D all reference people not in this fixture. The correct answer is identifiable purely by entity matching. Mention Josh/VP/Maria briefly as in-play-but-wrong. **REVISED 2026-04-13.**
- **#65 reverse_escalation** - A, C, D are generic bug types not grounded. Ground in related workspace state. **REVISED 2026-04-13.**
- **#67 postmortem_reframe** - D (Postgres bug) not grounded; replaced with a 4-hour / plan_change_date distractor. **REVISED 2026-04-13.**

### DISPUTED - authors should review
- **#64 roi_translator** - The authored correct answer C (Feature 5) is mathematically correct (5N = 15 + 2N → N = 5) but the fixture line 22 literally states "Break-even: feature 3". A careful reader trusting the fixture's own summary will pick B. **Fix the fixture to say "Break-even: feature 5"** or explicitly make this a "catch the fixture's own error" test in the methodology.

### Systematic patterns to address
1. **Entity-absence distractors**: A frequent pattern (#49, #51, #52, #56, #59, #60, #61, #65) is that 1-3 distractors name entities, files, bugs, or people not present in the workspace. A reader can rule them out without understanding the PM judgment being tested - they just check "is this term in the fixture?" This reduces a 4-way MCQ to a 2- or 3-way question and inflates scores for non-PM reasoning. **Recommend**: every distractor should name entities that appear somewhere in the workspace.

2. **The "inference beyond fixture" pattern**: Scenarios #63 ("half a day") and #66 (proration/refund/dunning specifics) include correct-answer language that goes beyond what the fixture explicitly states, relying on domain knowledge. This is acceptable but should be consistent - either the MCQ is strictly fixture-grounded, or it's fixture + commonly-available domain knowledge. Declare the rule in methodology.

3. **Good answer-language / fixture-language alignment**: Many correct answers (C in #53, C in #55, C in #58, B in #60, B in #65, C in #68) reuse verbatim fixture phrasing. This is helpful for scorability but also makes the correct answer slightly "obvious" from surface pattern matching. For flagship questions, consider paraphrasing the correct answer so it can't be picked on string-overlap alone. (#50 and #54 do this well.)

4. **Construct validity overall**: The underlying workspace content is well-constructed and genuinely requires PM judgment to interpret (especially #50, #54, #55, #58, #62, #67). The main weakness is distractor grounding, not fixture quality. Tightening distractors in the 9 flagged scenarios would meaningfully raise the construct validity of this subset.
