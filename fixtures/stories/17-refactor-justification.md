# Payment Service Health

## Current state
- Average time to add a new billing feature: 5 days
- Root causes of slowness:
  - Billing logic spread across 4 files with circular dependencies
  - No clear separation between Stripe API calls and business logic
  - Test setup requires 200 lines of mocking per test
  - Every change requires updating 3 different validation layers

## Proposed refactor
- Consolidate billing logic into a single module with clear interfaces
- Separate Stripe API adapter from business logic
- Create shared test fixtures
- Estimated effort: 3 weeks (Alan full-time)

## Impact projection
- Post-refactor feature development: ~2 days per feature (down from 5)
- Planned Q2 billing features: 6 features
- Current cost: 6 features x 5 days = 30 days
- Post-refactor cost: 3 weeks refactor + 6 features x 2 days = 27 days
- Break-even: feature 3 (estimated April delivery)

## CEO concern (from #leadership, March 5)
- 'We cannot afford 3 weeks without shipping. Customers are waiting.'
