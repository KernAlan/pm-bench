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
- Cumulative cost per N features (do-the-math):
  - N=3: without=15 days, with=15+6=21 days (refactor still behind)
  - N=5: without=25 days, with=15+10=25 days (break-even)
  - N=6: without=30 days, with=15+12=27 days (refactor 3 days ahead)
- Break-even at feature 5; net positive from feature 6 onward

## CEO concern (from #leadership, March 5)
- 'We cannot afford 3 weeks without shipping. Customers are waiting.'
