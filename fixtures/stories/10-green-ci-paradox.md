# CI / Test Health - March 8

## Test suite stats
- Total tests: 342
- Passing: 342 (100% green for 4 weeks straight)
- Last failure: February 8 (flaky network test, now mocked)
- Coverage: 78% line coverage
- Avg CI run time: 4 minutes

## Customer-reported bugs (same 4-week period)
- BUG-201 (Feb 12): Billing calculation wrong for mid-cycle plan change
- BUG-204 (Feb 18): Webhook delivery fails silently when payload > 1MB
- BUG-207 (Feb 25): Proration calculation off by 1 cent for annual plans
- BUG-211 (Mar 2): Race condition in concurrent subscription updates
- BUG-215 (Mar 5): Timezone-dependent billing cutoff produces wrong invoice date
- BUG-218 (Mar 7): Customer with 50+ subscriptions hits N+1 query, 30s page load

## Test distribution
- Unit tests (pure functions, no I/O): 280 (82%)
- Integration tests (with test database): 55 (16%)
- End-to-end tests (full API flow): 7 (2%)
- Edge case tests (boundary conditions, race conditions): 0 (0%)
- Load/performance tests: 0 (0%)
