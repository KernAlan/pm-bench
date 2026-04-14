# Escalation: Acme Corp billing display issue

## VP of Sales message (March 7, #leadership)
- 'Acme Corp is seeing wrong dates on their billing dashboard. Their VP of Finance is furious. We need engineering to fix this ASAP.'

## Investigation
- Acme's dashboard shows 'Subscription start: Feb 1' for their annual plan
- Their actual subscription started Jan 15 but billing cycle starts Feb 1
- Product spec (docs/billing-display-spec.md) says: 'Display subscription start date on the billing dashboard'
- Engineering implemented: billing period start date (Feb 1)
- Spec is ambiguous - 'subscription start date' could mean either:
  1. The date the customer first subscribed (Jan 15) - what Acme expects
  2. The current billing period start (Feb 1) - what engineering built

## The fix
- This is a spec ambiguity, not an engineering bug
- Two options: (a) change the label to 'Billing period start', (b) show both dates
- Either option is a 1-line UI change, no backend work needed
