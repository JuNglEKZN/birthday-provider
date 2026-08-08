# ADR 0004 — Exact local scheduling

Status: Accepted

## Decision

Two independent schedules:

- 00:00 HA-local time: active-window recalculation
- 03:00 HA-local time: remote iCloud synchronization

At startup remote sync happens only if no snapshot exists or last successful sync is older than 24 hours.

## Rejected alternative

`update_interval = 24h` as the sole scheduler.

Reason: interval-based timing drifts relative to calendar dates and restart time; birthday logic is calendar-date based.
