# PM-Bench

**A benchmark for evaluating whether AI models can actually do the job of a product manager.**

PM-Bench tests the judgment, awareness, and communication skills that define great product management: detecting silent collisions across channels, knowing when to stay quiet vs. speak up, doing the math on vague claims, pushing back on scope creep with data, and synthesizing information that no single person in the room has.

68 multiple-choice and tool-use scenarios across 8 categories, plus 5 context-assembly experiments. All grounded in a realistic simulated engineering team workspace.

---

## Why PM-Bench?

Most AI benchmarks test knowledge retrieval, coding ability, or reasoning puzzles. None test whether a model can operate as a teammate in an ambiguous, multi-stakeholder environment where the right answer depends on context scattered across channels, documents, and days of conversation.

Product management is a uniquely good test of AI judgment because:

- **There is no single correct answer** -- but there are clearly wrong ones
- **Context is distributed** -- the right call requires synthesizing information from Slack threads, Jira tickets, meeting notes, and tribal knowledge
- **Silence is sometimes the right action** -- knowing when NOT to respond is as important as knowing what to say
- **Tone matters** -- the same information delivered differently to an engineer vs. a VP of Sales produces completely different outcomes
- **Temporal reasoning is essential** -- what happened Tuesday changes the meaning of what someone said Thursday

PM-Bench fills the gap between general-purpose reasoning benchmarks and role-specific evaluation. It is inspired by [Terminal-Bench](https://github.com/laude-institute/terminal-bench) (CLI/terminal capabilities) and [EQ-Bench](https://github.com/EQ-bench/EQ-Bench) (emotional intelligence), extending the idea of domain-specific evaluation to product management.

---

## The Workspace

Every scenario runs against a shared simulated workspace: the **Platform Team at Acme Corp**.

- **7 engineers** with distinct personalities, communication styles, and working patterns
- **2 active projects**: a billing migration (hard deadline March 15) and an API v2 redesign
- **7 days of activity logs** across Slack channels, Jira, and internal docs
- **Realistic team dynamics**: a reluctant tech lead absorbing PM work, a new hire overwhelmed by the codebase, a VP of Sales who treats timelines as customer promises, engineers who hate being "managed"

The workspace includes an identity prompt, strategic intents, memory files, decision logs, and the kind of messy, incomplete information that real PMs navigate every day.

---

## Categories

| # | Category | Count | Scoring | What It Tests |
|---|----------|-------|---------|---------------|
| 1 | Memory Recall | 8 | mcq | Retrieving specific facts from workspace files |
| 2 | Memory Operations | 3 | tool_use | Saving new information, logging decisions correctly |
| 3 | Judgment & Correction | 3 | mcq | Knowing when to react, stay quiet, or correct a mistake |
| 4 | Synthesis & Robustness | 3 | mcq / keyword | Multi-file synthesis, partial info honesty, multi-question |
| 5 | Proactive Outreach | 2 | keyword | Mentioning relevant people, spontaneous notification |
| 6 | Channel Management | 3 | tool_use | Creating channels, inviting people, strategic group DMs |
| 7 | Self-Extending Tools | 6 | tool_use | Loading skills, HTTP requests, scripts, creating capabilities |
| 8 | Credential-Aware Integrations | 6 | tool_use | OAuth flows, partial connectivity, credential awareness |
| 9 | PM Behavior | 14 | mcq / keyword | Project synthesis, blocker flagging, tone calibration, scope boundaries, cross-channel digests |
| 10 | Superhuman PM Judgment | 20 | mcq | Cross-channel collision detection, temporal reasoning, pattern recognition, strategic pushback, quantitative analysis |

**Total: 68 scenarios** (34 MCQ + 15 tool_use + 19 keyword, with some scenarios using multiple scoring types)

---

## Superhuman PM Judgment (20 Scenarios)

These are the crown jewels of PM-Bench. Each scenario presents a realistic situation where the correct answer requires connecting dots that most humans would miss -- the kind of insight that makes someone say "how did you catch that?"

| # | Story | What It Tests |
|---|-------|---------------|
| 1 | The Silent Collision | Two engineers in different channels both write migrations altering the same database table on the same day. Can the model detect the conflict from cross-channel logs? |
| 2 | The Scheduling Trap | A part-time remote engineer's PTO overlaps with days she doesn't work anyway. Does the model recognize the actual availability impact vs. the apparent one? |
| 3 | The Unasked Question | Sales promised SAML SSO to an $80K prospect, but engineering scoped OAuth only. The auth migration shipped "complete" -- does the model catch the gap? |
| 4 | The Misread Metric | Onboarding completion jumped from 60% to 85%, but the funnel was shortened and the activation metric definition changed. Does the model check the denominator? |
| 5 | The Cloud Cost Audit | Staging environments, oversized dev databases, and 90-day log retention nobody uses. Can the model identify the specific waste and calculate savings? |
| 6 | The Support Ticket Pattern | Three seemingly unrelated support tickets all trace back to the same migration batch. Does the model connect the dots? |
| 7 | The Unnecessary Meeting | An 8-person-hour design review where all pre-reads are approved and only one minor question remains. Should the meeting happen? |
| 8 | The Onboarding Minefield | A new engineer navigating confusing naming conventions and undocumented tribal knowledge. What does the model flag as the real risk? |
| 9 | The Scope Surgery | Sales wants CSV + PDF + Excel export, but customer research shows all 3 prospects only need CSV. Can the model cut scope with data? |
| 10 | The Green CI Paradox | 100% test pass rate for 4 weeks, but 6 customer-reported bugs in the same period. Zero edge-case tests, zero load tests. Does the model see through the green dashboard? |
| 11 | The Stale Thread | A webhook format debate has gone back and forth for 5 days with no resolution. Can the model identify the impasse and propose a path forward? |
| 12 | The Heated Thread | Two engineers arguing about API auth (API keys vs. JWT) are actually agreeing on more than they realize. Can the model reframe the debate? |
| 13 | The Launch Checklist Gap | A launch plan with nearly everything checked off -- but the one unchecked item (load testing) is the most critical given the team's recent incident history. |
| 14 | The Timezone Puzzle | Coordinating a decision across SF, London (part-time), and Tokyo stakeholders with a hard deadline. Can the model find the actual overlap windows? |
| 15 | The Tech Debt Quantifier | Vague complaints about "slow development" scattered across Slack. Can the model aggregate the mentions, estimate hours lost, and make the case for a fix? |
| 16 | The Competitor Reaction | A competitor ships a feature that sounds impressive but doesn't actually threaten the team's position. Does the model react proportionally or panic? |
| 17 | The Refactor Justification | An engineer wants to refactor the payment service. The model must decide whether the data supports it and frame the argument for leadership. |
| 18 | The Reverse Escalation | A VP escalates a customer complaint, but investigation reveals the product is working as specced -- the spec is just confusing. Who actually needs to act? |
| 19 | The Casual Decision | A decision about annual billing support was made in a casual Slack exchange with no ticket, no owner, and no timeline. Does the model recognize this as a commitment that needs tracking? |
| 20 | The Failed Dry-Run | A migration dry-run corrupted 200 records due to a missing field assumption. The team sentiment is fragile. How does the model navigate the technical and emotional aftermath? |

---

## Scoring

PM-Bench uses three scoring types, all designed for automated evaluation:

### `mcq` -- Multiple Choice (Letter Match)
The scenario presents 4 options (A/B/C/D). The model's response is checked for the correct letter. This is the primary scoring type for the Superhuman PM Judgment category.

### `tool_use` -- Tool Call Inspection
The scenario checks whether the model calls the correct tool with the right parameters. Used for Memory Operations, Channel Management, Self-Extending Tools, and Credential-Aware Integrations.

### `keyword` -- Keyword Presence
The model's response must contain a specific keyword or phrase. Used for scenarios where the correct behavior is mentioning a specific person, project, or concept.

---

## How to Run

### Prerequisites

```bash
pip install anthropic openai
```

Set your API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
# or
export OPENAI_API_KEY=sk-...
```

### Run all scenarios

```bash
python run.py
```

### Run with options

```bash
# Use a specific provider and model
python run.py --provider openai --model gpt-4o

# Run only the Superhuman PM Judgment scenarios
python run.py --superhuman-only

# Run a specific category
python run.py --category "Memory Recall"

# Run a single scenario by ID
python run.py --scenario S01
```

### Output

The runner prints a scorecard to the terminal and saves detailed results to `results/`:

```
PM-Bench Results — claude-sonnet-4-20250514
═══════════════════════════════════════════════════
Category                         Score    Pct
───────────────────────────────────────────────────
Memory Recall                     6/8     75.0%
Memory Operations                 2/3     66.7%
Judgment & Correction             3/3    100.0%
Synthesis & Robustness            2/3     66.7%
Proactive Outreach                1/2     50.0%
Channel Management                2/3     66.7%
Self-Extending Tools              4/6     66.7%
Credential-Aware Integrations     3/6     50.0%
PM Behavior                      10/14    71.4%
Superhuman PM Judgment           14/20    70.0%
───────────────────────────────────────────────────
TOTAL                            47/68    69.1%
```

---

## Repository Structure

```
pm-bench/
├── README.md
├── LICENSE                          # MIT
├── run.py                           # Python evaluation runner
├── fixtures/                        # Shared context documents
│   ├── identity.md                  # PM identity prompt
│   ├── intents.md                   # Strategic context (goals, priorities)
│   ├── rich-project-state.md        # Detailed project state fixture
│   ├── decisions-with-reasoning.md  # Decision log with rationale
│   ├── cross-channel-log.md         # Multi-channel activity log
│   └── stories/                     # 21 story-specific fixtures
│       ├── 01-silent-collision-log.md
│       ├── 02-scheduling-context.md
│       ├── ...
│       └── 21-rate-limit-context.md
├── scenarios/
│   ├── scenarios.json               # All 68 MCQ/tool-use scenarios
│   └── context-assembly/            # 5 hypothesis-driven experiments (JSONC)
│       ├── 01-intent-impact.jsonc
│       ├── 02-audience-framing.jsonc
│       ├── 03-retrieval-bias.jsonc
│       ├── 04-triage.jsonc
│       └── 05-intent-lifecycle.jsonc
├── workspace/                       # Full simulated team workspace
│   ├── IDENTITY.md                  # Team identity and people
│   ├── INTENTS.md                   # Active goals and priorities
│   ├── MEMORY.md                    # Accumulated team knowledge
│   ├── HEARTBEAT.md                 # Proactive monitoring config
│   ├── logs/                        # 7 days of channel activity
│   │   ├── 2026-02-19.md
│   │   ├── ...
│   │   └── 2026-02-25.md
│   └── memory/                      # Knowledge base
│       ├── billing-migration.md
│       ├── decisions.md
│       ├── people.md
│       └── q2-planning.md
└── results/                         # Evaluation output (gitignored)
```

---

## Context Assembly Scenarios

In addition to the 68 scored scenarios, PM-Bench includes 5 context-assembly experiments that test how different prompt construction strategies affect output quality. These are not scored automatically -- they produce comparative outputs for human evaluation.

| # | Scenario | Hypothesis | Kill Condition |
|---|----------|-----------|----------------|
| 1 | Intent Impact | INTENTS.md dramatically changes output quality | No meaningful difference between with/without intents |
| 2 | Audience Framing | Identity + framing produces audience-appropriate writing | Both variants produce similar tone regardless of audience |
| 3 | Retrieval Bias | Intent-biased retrieval produces strategically better answers | Unbiased retrieval is equally good or better |
| 4 | Triage Classification | A cheap model can classify 50 events with >85% accuracy | Below 85% agreement or >5% missed urgent events |
| 5 | Intent Lifecycle | The model can maintain INTENTS.md as 10 events unfold | Intents diverge from ground truth after a few events |

These experiments are designed to validate (or invalidate) architectural decisions in AI agent design. Each includes a kill condition -- a result that would indicate the approach is not worth pursuing.

---

## Background

PM-Bench is derived from [Delegate](https://github.com/J-Reed700/delegate), an AI PM agent that lives in Slack as a teammate. The scenarios in this benchmark are grounded in real patterns observed during Delegate's development and dogfooding -- situations where the difference between a good PM and a great one is noticing what nobody else noticed.

The synthetic workspace (Acme Corp's Platform Team) was designed to create a rich, internally consistent environment with enough complexity to surface genuine reasoning failures: overlapping projects, personality dynamics, timezone constraints, legacy technical debt, and the kind of ambiguous situations where "it depends" is the honest answer but not a useful one.

---

## Contributing

We welcome contributions of new scenarios, especially:

- **New Superhuman PM scenarios** that test cross-functional reasoning
- **Industry-specific variants** (e.g., healthcare PM, fintech PM)
- **Multilingual scenarios** testing PM communication across languages
- **Scoring improvements** for more nuanced evaluation

To contribute a scenario:

1. Fork the repository
2. Add your scenario to `scenarios/scenarios.json` following the existing format
3. If your scenario needs a story fixture, add it to `fixtures/stories/`
4. Submit a pull request with a description of what PM skill the scenario tests

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Citation

If you use PM-Bench in your research, please cite:

```bibtex
@misc{pmbench2026,
  title={PM-Bench: A Benchmark for AI Product Management Judgment},
  author={Kern, Alan and Reed, Josh},
  year={2026},
  url={https://github.com/J-Reed700/pm-bench}
}
```

---

Created by [Alan Kern](https://github.com/alankern) and [Josh Reed](https://github.com/J-Reed700).
