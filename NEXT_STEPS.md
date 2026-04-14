# Next Steps to True Gold Standard

This document tracks what PM-Bench v1.0 has vs. what it still needs to be a fully-realized, community-validated benchmark.

## ✅ What's built (autonomous work complete)

### Benchmark content
- [x] 68 MCQ/keyword/tool_use scenarios across 10 categories
- [x] 20 open-ended scenarios with rubric + LLM-judge scoring
- [x] 5 context-assembly experiments with kill conditions
- [x] Simulated team workspace (7 engineers, 2 projects, 7 days of logs)
- [x] 21 story-specific fixture documents
- [x] Self-audit of all 20 Superhuman scenarios (1 fixture bug fixed)
- [x] Distractor quality improvements for 8 scenarios

### Evaluation infrastructure
- [x] Python runner (`run.py`) — Anthropic, OpenAI, Mock providers
- [x] Open-ended mode with rubric + LLM-judge scoring
- [x] Mock provider for end-to-end testing without API keys (3 modes)
- [x] MCQ scorer robust to 15+ answer formats (122 unit tests)
- [x] Integrity regression tests
- [x] GitHub Actions CI

### Analysis tooling
- [x] Item Response Theory analysis (`tools/analyze.py`)
- [x] Multi-model answer-key validation (`tools/validate_answers.py`)
- [x] Paraphrase-based contamination detection (`tools/contamination.py`)
- [x] Multi-model baseline orchestrator (`tools/multi_run.py`)
- [x] Post-run report generator (`tools/report.py`)
- [x] Result comparison/diff tool (`tools/compare_results.py`)
- [x] Workspace variant generator for anti-memorization (`tools/workspace_variants.py`)
- [x] Schema validation CLI (`tools/validate_schema.py`)

### Documentation
- [x] `README.md` with badges
- [x] `METHODOLOGY.md` (~3000 words: construct, scoring, limitations)
- [x] `PAPER.md` (~7000 words, NeurIPS D&B-style draft)
- [x] `docs/CONSTRUCT_VALIDITY.md` (per-scenario audit)
- [x] `HOW_TO_RUN.md` (step-by-step walkthrough)
- [x] `CHANGELOG.md`, `BENCHMARK_VERSION.md`, `CITATION.cff`

### Community infrastructure
- [x] `LEADERBOARD.md` (awaiting first submissions)
- [x] `SUBMISSIONS.md` (submission protocol)
- [x] `HUMAN_BASELINE.md` (protocol for human PM baselines)
- [x] `CONTRIBUTING.md`
- [x] `submissions/` and `human_baselines/` directories

### Reproducibility & packaging
- [x] `pyproject.toml` with optional extras
- [x] `Dockerfile` + `docker-compose.yml` + `.dockerignore`
- [x] `pm-bench` CLI entry point
- [x] `VERSION` file
- [x] `examples/sample_result.json`
- [x] HuggingFace dataset preparation (`huggingface/`)

---

## ⏳ What requires API keys (infrastructure ready)

All tools are built. User supplies API keys and runs them.

### 1. Baseline scores across multiple models

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...

# Run MCQ Superhuman 20 against multiple models, 3 iterations each
python tools/multi_run.py \
    --iterations 3 \
    --models claude-sonnet-4-20250514 gpt-4o claude-opus-4-20250514 \
    --modes mcq open-ended \
    --superhuman-only
```

Expected output: `analysis/baselines.md` with mean ± 95% CI for each model.

**Cost estimate:** ~$5-15 per model per mode for 3 iterations of 20 scenarios.

### 2. Multi-model answer-key validation

```bash
python tools/validate_answers.py \
    --models claude-sonnet-4-20250514 gpt-4o claude-opus-4-20250514 gemini-1.5-pro \
    --provider-map 'claude-sonnet-4-20250514:anthropic,gpt-4o:openai,claude-opus-4-20250514:anthropic,gemini-1.5-pro:openai'
```

Expected output: `analysis/answer_validation.csv` with Fleiss' kappa and disputed items.

### 3. Contamination analysis

```bash
python tools/contamination.py \
    --model claude-sonnet-4-20250514 \
    --paraphraser-model gpt-4o \
    --n-scenarios 20
```

Expected output: `analysis/contamination_report.md` with original vs. paraphrased accuracy.

### 4. Item analysis

Run after baselines exist:
```bash
python tools/analyze.py
```

Expected output: `analysis/item_stats.csv` and `analysis/analysis_report.md` with difficulty, discrimination, ceiling/floor items.

### 5. Fill paper § 5 with real results

Once baselines exist, replace `[PLACEHOLDER]` sections in `PAPER.md` with actual numbers.

---

## 🧑 What requires human volunteers

### 1. Human PM baselines

Protocol is documented in `HUMAN_BASELINE.md`. To reach GPQA-level credibility, target:
- 5+ experienced PMs (3+ years experience)
- Each completes Superhuman 20 MCQ under timed conditions
- Report human accuracy baseline + per-scenario human agreement

**Target numbers from reference benchmarks:**
- GPQA: 61 PhDs validated 198 questions
- ARC-AGI-2: 400+ humans, every task solved by 2+
- PRBench: 182 professionals achieved 93.9% agreement

### 2. Inter-annotator agreement on scenarios

Have 2-3 independent annotators answer the Superhuman 20 under the same conditions. Compute Cohen's kappa between annotators and vs. authored answers.

Target: κ > 0.8 for a reliable benchmark. Items with κ < 0.6 should be flagged for revision or removal.

---

## 🌐 What requires external publication

### 1. HuggingFace dataset push

```bash
export HF_TOKEN=<your token>
python tools/hf_push.py --repo-id KernAlan/pm-bench
```

Makes the benchmark loadable via `datasets.load_dataset("KernAlan/pm-bench", "mcq")`.

### 2. Paper submission to NeurIPS Datasets & Benchmarks track

`PAPER.md` is draft-ready. Once baselines are in:
1. Convert to LaTeX (use [pandoc](https://pandoc.org/))
2. Target NeurIPS 2026 Evaluations & Datasets track (deadline typically May-June)
3. CC by 4.0 for paper, MIT for dataset (already set)

### 3. Announcements

- Post on arXiv (cs.CL category)
- Announce on Twitter/X, HackerNews, r/MachineLearning
- Tag Anthropic, OpenAI, Google DeepMind researchers working on agent evaluation

---

## Gold standard scorecard

What separates a respected benchmark from a curio:

| Criterion | Reference (Gold Standard) | PM-Bench v1.0 Status |
|-----------|---------------------------|----------------------|
| Scenario count (post-curation) | 89 (Terminal-Bench), 198 (GPQA Diamond), 171 (EQ-Bench v2) | 68 MCQ + 20 open-ended + 5 experiments |
| Independent validation | GPQA: 61 PhDs; SWE-bench: 93 devs (3 per item) | Self-audit done; multi-model + human pending |
| Inter-annotator agreement | κ > 0.8 standard; PRBench 93.9% | Infrastructure ready; not yet measured |
| Published baselines | 16 models (Terminal-Bench 2.0) | 0 — requires API keys |
| Human baselines | 77% (ARC-AGI-1 Mechanical Turk), 74% (GPQA) | 0 — protocol published |
| Contamination mitigation | LiveBench rotates monthly; SWE-bench Live post-2024 | Variant generator + paraphrase check ready |
| Reproducibility | Code, data, Dockerized | ✅ pyproject, Docker, CI |
| Peer review | NeurIPS D&B track | Paper draft ready; not submitted |
| HuggingFace release | Most benchmarks now on HF hub | Preparation done; push pending |

**Honest assessment:** The infrastructure is at gold-standard level. The empirical gap is real and significant. Closing it requires API credits, human volunteers, and public release — none of which can happen autonomously.

---

## Recommended sequence for the user

1. **Week 1:** Run baselines (3 models × 3 iterations × 2 modes). Cost: ~$50-150. Fill paper § 5.
2. **Week 1:** Run answer-key validation. Flag any disputed items. Possibly revise 1-3 scenarios.
3. **Week 1:** Run contamination analysis on baseline model. Document findings.
4. **Week 2:** Recruit 3-5 experienced PMs for human baselines. Compensate if possible.
5. **Week 2:** Push to HuggingFace. Announce.
6. **Week 3-4:** Convert paper to LaTeX, submit to arXiv.
7. **Week 4+:** Submit to NeurIPS 2026 Evaluations & Datasets track when CFP opens.

Total time to "submitted paper with real data": ~4 weeks of part-time work.
Total external costs: $100-300 for API baselines + optional human baseline compensation.
