# Incident Report — March 6 billing migration dry-run failure

## What happened
- Ran billing migration dry-run against production data snapshot
- Migration script corrupted 200 customer subscription records
- Records showed incorrect plan tiers and billing amounts
- Took 4 hours to identify all affected records and restore from backup

## Timeline
- 09:00 Alan started dry-run against prod snapshot
- 09:12 Sarah's monitoring alert fired — data anomalies detected
- 09:15 Alan confirmed corruption, stopped script
- 09:30 Josh sent customer communication (no actual customer impact since this was a snapshot, not prod)
- 13:00 All records restored, root cause identified

## Root cause
- Migration script assumed all subscriptions have a `plan_change_date` field
- 200 legacy subscriptions (pre-2025) don't have this field
- Script wrote null values into required columns, triggering cascading data integrity issues

## What went right
1. Sarah's monitoring caught it in 12 minutes (alert threshold: 15 min)
2. Alan's rollback script (written last month) worked perfectly
3. Customer communication went out within 30 minutes (template was pre-written)

## What went wrong
1. Migration script wasn't tested against production-scale data with full historical records (legacy accounts missing expected fields)

## Team sentiment (from retrospective)
- Alan: 'I should have caught the null field issue. Feeling pretty bad about this.'
- Sarah: 'At least monitoring worked. But we got lucky it was a dry-run.'
- Josh: 'CEO asked me what happened. Not a fun conversation.'
