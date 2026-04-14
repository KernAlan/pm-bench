# Changelog

All notable changes to PM-Bench will be documented here. Follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Open-ended evaluation mode with rubric + LLM-judge scoring (20 scenarios)
- Mock LLM provider for end-to-end pipeline testing without API keys
  (`--provider mock`, `--mock-mode perfect|random|weak`)
- HuggingFace dataset preparation (`huggingface/`)
- Workspace variant generator for contamination resistance (`tools/workspace_variants.py`)
- Post-run report generator (`tools/report.py`)
- Result comparison/diff tool (`tools/compare_results.py`)
- Integrity regression test (`tools/integrity_check.py`)
- Scenario self-audit (`docs/CONSTRUCT_VALIDITY.md`)
- Dockerfile + docker-compose for reproducibility
- Discourse-level MCQ answer patterns ("ultimately, X is the answer",
  "therefore B", "X is right", "my answer: X", "final answer: X")

### Fixed (post-audit)
- Scenario #64 (roi_translator) fixture contradicted itself ("break-even:
  feature 3" vs actual math showing feature 5). Fixture now shows
  step-by-step cumulative-cost derivation. Authored correct_answer unchanged.

### Documented
- Distractor quality audit in docs/CONSTRUCT_VALIDITY.md: ~9 of 20
  Superhuman scenarios have at least one "entity-absence" distractor
  (names something not in the workspace, making it rule-out-able without
  PM reasoning). Planned for v1.1 improvement.

## [1.0.0] — 2026-04-13

### Added
- 68 MCQ/keyword/tool_use scenarios across 10 categories
- 20 open-ended scenarios with rubric + LLM-as-judge scoring
- 5 context-assembly experiments (JSONC)
- Simulated team workspace (Acme Platform Team, 7 engineers, 7 days of logs)
- Python evaluation runner (`run.py`) supporting Anthropic and OpenAI
- Item Response Theory analysis tool (`tools/analyze.py`)
- Multi-model answer-key validation tool (`tools/validate_answers.py`)
- Paraphrase-based contamination detection (`tools/contamination.py`)
- Multi-model baseline orchestrator (`tools/multi_run.py`)
- Schema validation CLI (`tools/validate_schema.py`)
- Comprehensive pytest suite for scoring
- GitHub Actions CI
- METHODOLOGY.md — construct validity, scoring methodology, limitations
- PAPER.md — NeurIPS Datasets & Benchmarks-style paper draft
- LEADERBOARD.md, SUBMISSIONS.md, HUMAN_BASELINE.md, CONTRIBUTING.md

### Fixed
- Harmonized identity.md (removed team-specific dogfooding context for coherence across scenarios)
- MCQ scorer false-positive rejection ("Not B. C is correct." correctly identifies C)
- MCQ scorer handles prose formats: "X because", "pick X", "option X", em-dash delimiters
- Runner/data schema alignment
- Tool_use scenarios always excluded from runner (no harness) with clear messaging

### Known limitations
- No independent human validation of answer keys (tooling ready, requires contributors)
- No baseline results from major models (tooling ready, requires API keys)
- Single domain (software engineering)
- Single workspace design
