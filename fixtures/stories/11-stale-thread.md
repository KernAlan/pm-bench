# Thread: Webhook payload format (#billing-migration)
Started: 2026-03-03

- Mar 3, 09:00 Alan: Proposal: nest all billing fields under a 'billing' key
- Mar 3, 14:00 Sarah: I'd prefer flat structure - easier to parse on the consumer side
- Mar 3, 16:00 Alan: Nested is cleaner for versioning though
- Mar 4, 09:30 Sarah: Flat is what Stripe does and our customers expect that pattern
- Mar 4, 11:00 Alan: Good point about Stripe. But our payload has 3 distinct sections (billing, user, metadata) - flat would be 40+ top-level fields
- Mar 4, 15:00 Sarah: What about flat within sections? billing_plan_id, billing_amount, etc.
- Mar 5, 09:00 Alan: That's just nested with underscores. Same problem, worse DX.
- Mar 5, 14:00 Sarah: Let me think about it more
- Mar 6, 10:00 Alan: Any thoughts? This is blocking the webhook implementation
- Mar 6, 15:00 Sarah: Still mulling. Both approaches have tradeoffs.
- Mar 7, 09:00 Alan: We need to decide this week or we miss the March 15 deadline for webhook format lock
