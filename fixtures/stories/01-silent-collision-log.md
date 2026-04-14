# Daily Log - 2026-03-07

## #billing-migration
- 09:00 Alan: Starting on the events table changes for webhook tracking. Adding a `webhook_status` column and a `delivery_attempts` counter.
- 10:30 Alan: Migration file `20260307_add_webhook_status.sql` is ready. Alters the `events` table. Will PR after lunch.
- 14:00 Alan: PR #312 up - events table migration + webhook status tracking.

## #api-v2
- 09:30 Sarah: Working on subscription event processing today. Need to add a `delivery_state` enum column to the `events` table for tracking API v2 event lifecycle.
- 11:00 Sarah: Migration file `20260307_add_delivery_state.sql` ready. Alters the `events` table - adds `delivery_state` and `processor_version`.
- 15:00 Sarah: PR #313 up - event lifecycle tracking for API v2.

## #general
- 08:00 Josh: morning all
- 16:00 Josh: heading out, see everyone tomorrow
