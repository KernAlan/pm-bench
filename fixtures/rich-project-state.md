# Project State

## Billing Migration (Phase 2)
- **Owner**: Alan (lead), Sarah (auth/webhooks)
- **Status**: In progress — Phase 1 shipped Feb 20
- **Target**: March 31 launch
- **Blocker**: Ticket #847 — 847 legacy subscriptions need reconciliation before cutover. Alan working through them but estimates 2 more weeks.
- **Risk**: If reconciliation slips past March 15, we miss the March 31 target. No buffer.
- **Dependency**: Webhook format must be finalized before Sarah can start API v2 integration work. Sarah is blocked on this.
- **Note**: Sarah works M/W/F only (part-time)

## API v2
- **Owner**: Sarah (lead), Josh (review)
- **Status**: Design phase — waiting on billing webhook format
- **Target**: April 15
- **Blocker**: Cannot finalize endpoint contracts until billing webhook format is locked. Sarah has draft endpoints but can't validate them.
- **Dependency**: Depends on Billing Migration webhook format decision
- **Risk**: 2-week cascade delay if billing webhook slips

## Onboarding Flow (shipped)
- **Owner**: Josh
- **Status**: Shipped Feb 28
- **Result**: 40% reduction in time-to-first-value
- **Notes**: Used progressive disclosure pattern. Analytics show 85% completion rate.
