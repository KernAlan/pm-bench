# Decisions

## 2026-02-15 - Database: Postgres over alternatives
- **Decision**: Use Postgres for billing ledger
- **Alternatives considered**:
  - DynamoDB - rejected: poor fit for relational billing queries, eventual consistency unacceptable for financial data
  - MongoDB - rejected: schema flexibility not needed, Postgres JSONB covers our semi-structured needs without sacrificing ACID
- **Decided by**: Alan + Josh
- **Rationale**: Team has deep Postgres expertise, need strong transactional guarantees for billing, and JSONB handles the flexible metadata fields

## 2026-02-20 - Hiring freeze through Q1
- **Decision**: No new hires until April
- **Alternatives considered**:
  - Contractor for billing migration - rejected: onboarding cost too high for 6-week project, context transfer risk
  - Freelance frontend - deferred: revisit in April if onboarding metrics plateau
- **Decided by**: Alan
- **Rationale**: Burn rate discipline, want to prove PMF before expanding team
