# Slack mentions of workarounds - last 30 days

## Hardcoded API URL (from sprint Feb 10)
- Feb 12, Alan: 'had to manually change the billing URL in 3 places for staging'
- Feb 19, Alan: 'same URL issue again, lost 20 min finding all the hardcoded spots'
- Mar 3, Josh: 'billing tests failed because the URL was pointing at prod, who changed it?'
- Mar 5, Alan: 'URL thing bit me again, 30 min wasted'
- **Estimated cost**: ~1 hour/week across team

## Retry logic without backoff (from sprint Jan 27)
- Feb 8, Sarah: 'webhook endpoint got hammered - our retry has no backoff, sent 200 requests in 10 seconds'
- Feb 22, Alan: 'customer complained about duplicate webhooks, same retry issue'
- Mar 1, Sarah: 'manually adding delays to retry calls, this needs a real fix'
- **Estimated cost**: ~45 min/week + customer impact

## Generic error messages (from sprint Feb 3)
- Feb 10, Josh: 'customer ticket, they got "something went wrong" - spent 30 min reproducing to find the actual error'
- Feb 24, Alan: 'billing error, logs just say "error processing request" - had to add debug logging, find the issue, then remove the debug logging'
- Mar 6, Josh: 'another "something went wrong" ticket, 45 min to diagnose'
- **Estimated cost**: ~1 hour/week

## Skipped test (from sprint Jan 20)
- Jan 20, Sarah: 'skipping the webhook integration test for now, it's flaky'
- Feb 5, Alan: 'that skipped test would have caught BUG-204 (webhook >1MB failure)'
- Mar 7, Josh: 'should we re-enable the webhook test? it's been skipped 7 weeks'
- **Estimated cost**: missed bugs in production

## Total estimated weekly cost: ~2.75 hours/week (+ missed bugs)
