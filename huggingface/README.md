---
license: mit
task_categories:
- question-answering
- text-generation
language:
- en
tags:
- benchmark
- product-management
- ai-agents
- llm-evaluation
- judgment
size_categories:
- n<1K
pretty_name: PM-Bench
configs:
- config_name: mcq
  data_files: mcq.jsonl
- config_name: open-ended
  data_files: open-ended.jsonl
---

# PM-Bench

**A benchmark for AI PM judgment in a noisy engineering workspace.**

PM-Bench tests whether an AI teammate operating in a messy, multi-channel
engineering environment can notice the important thing, connect distributed
context, react with the right level of intervention, and communicate it in a
PM-shaped way.

- **68 MCQ / keyword scenarios** across 10 categories
- **20 open-ended scenarios** with rubric + LLM-judge scoring (tests unprompted judgment)
- Grounded in realistic simulated team workspaces with real PM failure modes:
  hidden dependencies, misleading metrics, missing commitments,
  single-point-of-failure risk, and knowing when to stay quiet.

Upstream repository: <https://github.com/KernAlan/pm-bench>

## What PM-Bench tests (and doesn't)

PM-Bench tests **PM-style inference** — can the model recover the right insight
from distributed context when pointed at the right documents? It does not test
PM execution — it won't tell you whether a model can run a sprint planning
meeting, write a PRD, or navigate a difficult stakeholder conversation in real
time.

The Superhuman PM Judgment scenarios (the core 20) are all multiple-choice.
That means the model sees four options and picks one. This is a meaningful
test of whether the model can connect dots across documents, but it's a weaker
test than "would the model notice this unprompted in a real Slack workspace?"
The open-ended subset removes the multiple-choice scaffolding and tests
whether the model surfaces the issue without being led to it.

## Dataset structure

### Configurations

| Config        | Size | Description                                                      |
|---------------|------|------------------------------------------------------------------|
| `mcq`         | 68   | Multiple-choice and keyword-scored scenarios (all categories)    |
| `open-ended`  | 20   | Rubric + judge-scored scenarios (mirror the Superhuman 20 MCQs)  |

A filter on `category == "Superhuman PM Judgment"` in the `mcq` config
yields the 20-item Superhuman subset.

### Fields

**`mcq` rows**
- `id` *(int)* — scenario ID (1-68)
- `name` *(string)* — short identifier
- `category` *(string)* — one of 10 categories (e.g. `Superhuman PM Judgment`)
- `scoring` *(string)* — `mcq`, `keyword`, or `tool_use`
- `context` *(string)* — rendered workspace files, concatenated with
  `--- filename ---` separators (fixture refs already resolved inline)
- `trigger` *(string)* — the user message / question
- `correct_answer` *(string)* — the correct letter or keyword
- `expected_tools` *(list[string])* — tool names a real agent would be
  expected to invoke, for reference only (not used by auto-scorers)

**`open-ended` rows**
- `id` *(int)* — open-ended scenario ID (1-20)
- `source_mcq_id` *(int)* — the matching MCQ scenario ID
- `name`, `category` — as above
- `context` *(string)* — rendered workspace, fixtures inlined
- `trigger` *(string)* — realistic PM task (no multiple-choice scaffolding)
- `must_mention` *(list[string])* — all required to pass the automated pre-check
- `should_mention` *(list[string])* — bonus signals for the judge
- `red_flags` *(list[string])* — phrases indicating the model missed the point
- `judge_prompt` *(string)* — scenario-specific instructions for the LLM judge

### Categories (MCQ)

Memory Recall, Memory Operations, Judgment & Correction, Synthesis &
Robustness, Proactive Outreach, Channel Management, Self-Extending Tools,
Credential-Aware Integrations, PM Behavior, and Superhuman PM Judgment.

## Intended use

PM-Bench is intended for:

- **Evaluating LLMs as PM/teammate agents** — measuring cross-document
  reasoning, temporal awareness, and "notice the important thing" behavior.
- **Research on judgment-style benchmarks** — item analysis, discrimination,
  contamination study.
- **Comparative model evaluation** — ranking models by their PM-judgment
  capability, with particular attention to the Superhuman 20 subset.

It is **not** intended as a proxy for whether a model can "be a PM." A high
PM-Bench score indicates strong reading comprehension, cross-document
reasoning, and pattern recognition — not operational PM competence.

## How to load

```python
from datasets import load_dataset

# Full MCQ set (68 scenarios)
mcq = load_dataset("KernAlan/pm-bench", "mcq")

# Open-ended judgment set (20 scenarios)
oe = load_dataset("KernAlan/pm-bench", "open-ended")

# Superhuman subset (20 MCQ)
superhuman = mcq["train"].filter(lambda r: r["category"] == "Superhuman PM Judgment")

# Inspect a single row
row = mcq["train"][0]
print(row["trigger"])
print(row["correct_answer"])
```

The full workspace context is already rendered into `context`; there is no
fixture indirection on the Hub (the upstream repo uses `@fixtures/...` refs
that this release inlines).

## Licensing

MIT. See the upstream repository for the full license text. You may use and
redistribute PM-Bench scenarios for research or commercial evaluation with
attribution.

## Citation

```bibtex
@software{pm_bench_2026,
  author  = {Kern, Alan},
  title   = {{PM-Bench}: A Benchmark for AI PM Judgment in a Noisy Engineering Workspace},
  year    = {2026},
  url     = {https://github.com/KernAlan/pm-bench},
  license = {MIT}
}
```

## Ethical considerations

- **Fictional team members.** Scenarios reference fictional people ("Alan",
  "Josh", "Sarah", "Marcus", "Priya", etc.) in fictional workplace situations.
  Any resemblance to real people or companies is coincidental.
- **Fictional workplace dynamics.** The workspaces portray realistic-but-
  fabricated team frictions (missed commitments, misread metrics, coordination
  failures). They are not case studies and should not be read as descriptions
  of any real organization.
- **Judgment bias.** "Superhuman PM judgment" labels are authored by the
  dataset creators and encode a particular view of what a senior PM should
  notice. Models that disagree with the rubric may still produce reasonable
  outputs; scores should be interpreted alongside qualitative review.
- **Domain scope.** PM-Bench is Western-startup-tech-flavored. It does not
  cover hardware PM, non-English PM work, regulated-industry PM, or government
  PM contexts. Do not generalize scores beyond the domain.
- **LLM-judge loop.** Open-ended scoring uses an LLM judge; this creates a
  risk of self-bias if the subject and judge share a training family. The
  upstream runner defaults to cross-family pairs (e.g., Claude-subject,
  GPT-4o-judge) to mitigate this.
