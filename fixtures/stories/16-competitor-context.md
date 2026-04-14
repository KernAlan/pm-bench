# Competitive Intelligence

## Competitor changelog - March 6
- Rival Corp shipped webhook signature verification v2 with Ed25519 support
- Also added: customer-facing webhook delivery logs, retry dashboard
- Blog post: 'Why we moved beyond HMAC-SHA256 for webhook security'

## Our current state
- Webhook signatures: HMAC-SHA256 (industry standard, still secure)
- No customer-facing webhook logs or retry dashboard
- Sarah's webhook code already has a signature module - adding a new algorithm would be localized to that module

## Sales notes (from Josh, last 2 weeks)
- Acme Corp (Mar 1): 'Do you support Ed25519 webhook signatures? Our security team prefers it.'
- Pinnacle Inc (Mar 4): 'Rival Corp just added Ed25519. Do you have that?'
- No specific deals lost over this, but it's coming up in evaluation calls
