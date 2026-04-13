# Billing Migration Phase 2 — Launch Plan

## Pre-launch checklist
- [x] Reconciliation script handles all edge cases
- [x] Staging environment tested with production data snapshot
- [x] Rollback script tested and documented
- [x] Customer communication drafted (email + in-app banner)
- [x] Monitoring dashboards updated with billing-specific alerts
- [x] On-call rotation confirmed for launch week
- [ ] Load test with production traffic patterns (scheduled March 12)

## Webhook delivery
- New webhook system sends billing events to customer endpoints
- Retry logic: exponential backoff, max 5 attempts
- Dead letter queue for permanently failed deliveries
- **No delivery confirmation mechanism** — if a webhook is sent and the customer's endpoint returns 200 but doesn't actually process it, we have no way to know
- **No customer-facing delivery log** — customers can't see what webhooks were sent or retry them

## Rollback plan
- Database: point-in-time recovery to pre-migration snapshot
- API: feature flag to route traffic to v1 billing endpoints
- Estimated rollback time: 15 minutes
