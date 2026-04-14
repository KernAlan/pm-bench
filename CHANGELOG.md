# Changelog

All notable changes to PM-Bench are tracked here. Follows [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] - 2026-04-14

### Scenarios
- 68 scenarios across 10 categories:
  - Memory Recall (8), Memory Operations (3), Judgment & Correction (3),
  - Synthesis & Robustness (3), Proactive Outreach (2), Channel Management (3),
  - Self-Extending Tools (6), Credential-Aware Integrations (6),
  - PM Behavior (14), Superhuman PM Judgment (20)
- 20 open-ended scenario variants with rubric-based scoring (optional for harnesses that support it)
- 5 context-assembly experiments with explicit kill conditions
- Simulated team workspace: 7 engineers, 2 active projects, 7 days of cross-channel logs

### Harness
- Canonical harness: [Delegate](https://github.com/J-Reed700/delegate) Rust eval suite
- Non-Delegate-equivalent harnesses are not accepted on the canonical leaderboard
- Scoring: PASS / PARTIAL / FAIL per Delegate's `scoring.rs`; leaderboard reports (PASS + PARTIAL) / 68

### Baselines
- Delegate + gpt-4.1-mini → **88.2%**
- Delegate + gpt-5.4-mini → **88.2%**
- Delegate + gpt-5-nano → **66.2%**
- Anthropic, Google baselines pending

### Tools (scenario infrastructure only)
- `tools/validate_schema.py` - JSON Schema validation of scenario files
- `tools/workspace_variants.py` - procedural workspace variants for contamination resistance (`v2-neon`, `v3-helix`, `v4-orbit`)

### Documentation
- `README.md` - overview, canonical leaderboard, how to run
- `METHODOLOGY.md` - construct, limitations, reproducibility
- `LEADERBOARD.md` - Delegate + model scores
- `SUBMISSIONS.md` - submission requirements
- `HUMAN_BASELINE.md` - protocol for human-PM baselines
- `CONTRIBUTING.md` - scenario contribution process
- `docs/CONSTRUCT_VALIDITY.md` - per-scenario self-audit of Superhuman 20
- `CITATION.cff` - machine-readable citation

### Known limitations
- No independent human validation of answer keys
- No human PM baseline submissions yet
- Scenarios authored by 2 people, selection bias toward Delegate's tool surface
- Single domain (software engineering teams)
- Single workspace design (mitigated partly by workspace-variant tooling)
