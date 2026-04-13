# Third-Party API Usage

## Stripe API
- Rate limit: 100 requests/second (our current plan)
- Current usage (billing team): ~40 req/sec during peak (invoice generation)
- Current usage (API v2 team): 0 req/sec (not yet in production)

## Planned Stripe usage
### Billing team (Alan)
- Webhook processor: polls Stripe for payment confirmation
- Estimated peak: 60 req/sec (up from 40, due to new reconciliation checks)
- Runs during: invoice generation window (1am-3am PST daily) and on-demand when customers update plans

### API v2 team (Sarah)
- Subscription lookup endpoint: hits Stripe to verify current plan status
- Estimated peak: 35 req/sec (based on current API traffic patterns)
- Runs during: all hours (customer-facing endpoint)

## Combined peak estimate: 95 req/sec (60 + 35)
- This is at 95% of our 100 req/sec limit under NORMAL load
- During traffic spikes (typically 1.5-2x normal): 143-190 req/sec
- Stripe rate limit exceeded → 429 errors → customer-facing failures

## No shared client or caching layer exists — each team has their own Stripe SDK instance with independent connection pools
