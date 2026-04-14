# Active Context - March 8, 2026

## Confusing naming conventions (legacy)
- 'plan' and 'tier' and 'subscription' all refer to the same concept in different parts of the codebase
- billing_v1 tables use 'plan_id', billing_v2 uses 'tier_id', Stripe API calls it 'subscription'
- The migration script maps between all three - Alan calls this 'the rosetta stone file' (src/billing/mapping.rs)

## Tribal knowledge
- Never run billing tests against production Stripe keys - there's a .env.test file but it's not documented anywhere
- The 'events' table has a soft-delete pattern but the 'subscriptions' table uses hard deletes - this is intentional but confusing
- Sarah's webhook code uses a custom retry queue, not the standard job runner - she had perf issues with the standard one in January

## Current team dynamics
- Alan is heads-down on reconciliation and may be short in responses - it's not personal, he's under deadline pressure
- Josh is the best person to pair with for first week - he knows the full codebase and is patient with questions
- Sarah works M/W/F only - don't schedule anything with her on T/Th
