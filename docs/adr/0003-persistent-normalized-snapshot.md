# ADR 0003 — Persist normalized dataset, not active-only cache

Status: Accepted

## Decision

Persist the complete minimal normalized birthday dataset.

Do not use a precomputed `active.json`/active event cache as the source of truth.

## Reason

If iCloud is unavailable for several days, `days_until` in an active-only cache becomes stale.

A normalized birthday catalog can be recalculated locally against today's date indefinitely.
