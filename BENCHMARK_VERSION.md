# PM-Bench Versioning Policy

Benchmark scores must cite a version. Version numbers follow semver:

- **MAJOR** (e.g. 2.0.0): Breaking change to scenario set or scoring semantics. Previous scores are not comparable.
- **MINOR** (e.g. 1.1.0): Added/revised scenarios, new scoring modes, new infrastructure. Previous scores remain comparable for unchanged items.
- **PATCH** (e.g. 1.0.1): Bug fixes, doc corrections, tooling improvements that don't affect scoring outcomes.

## Current: v1.0.0

Released: 2026-04-13

Contents:
- 68 MCQ/keyword/tool_use scenarios
- 20 open-ended scenarios with rubric + LLM-judge scoring
- 5 context-assembly experiments
- Item Response Theory analysis tooling
- Multi-model validation tooling
- Paraphrase-based contamination detection
- Comprehensive pytest suite for scoring

## How to cite a score

Always include:
- PM-Bench version (e.g. "PM-Bench v1.0.0")
- Mode (MCQ Superhuman / MCQ Full / Open-Ended)
- Subject model (full version string)
- Judge model if open-ended
- Iteration count
- 95% CI

Example: "Claude Sonnet 4 scored 78.5% (±2.3%, N=5) on PM-Bench v1.0.0 MCQ Superhuman 20."

## Scoring algorithm stability

The MCQ extract_mcq_choice function has a pinned test suite (tests/test_scoring.py). Any change that alters outputs on existing test cases triggers a minor or major version bump. Patch versions may only add new test cases or refactor without behavior changes.
