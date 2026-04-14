# Daily Log - 2026-03-06

## #billing-migration
- 09:15 Alan: Found edge case in reconciliation - subscriptions with mid-cycle plan changes aren't mapping correctly. Need to handle ~120 of these.
- 09:45 Alan: Workaround identified, writing migration script for these cases
- 14:30 Sarah: Webhook format proposal posted in doc - need Alan's review before I can unblock API v2 work

## #api-v2
- 10:00 Sarah: Draft endpoint contracts ready for review (pending webhook format decision)
- 11:30 Josh: Reviewed Sarah's draft - looks good, just waiting on webhook format lock

## #general
- 08:00 Josh: good morning everyone
- 08:05 Alan: morning!
- 12:00 Josh: lunch break, back at 1
- 16:00 Alan: wrapping up for the day, reconciliation script handles 90 of 120 edge cases so far

## #deploys
- 13:00 deploy-bot: staging deployed v2.4.1 (3 commits)
- 13:05 deploy-bot: all health checks passing
- 15:30 Sarah: dashboard showing stale data after deploy - investigating
- 15:45 Sarah: fixed - cache TTL was set to 24h instead of 1h, hotfix deployed
