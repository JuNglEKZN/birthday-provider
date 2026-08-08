# Stage 4 — Scheduling and Fail-safe

## Goal

Implement deterministic daily behavior.

## Required behavior

### Local midnight

At 00:00 HA-local time:

- recalculate active events from cached normalized birthdays
- do not contact iCloud

### Remote sync

At 03:00 HA-local time:

- execute one remote iCloud full sync
- persist only after complete success
- update last_successful_sync
- recalculate active events

### Startup

- load cache
- calculate active immediately
- remote sync only if no snapshot or last successful sync >24h old

### Unload

Cancel every scheduled listener.

## Tests

Use time-freezing/HA helpers as appropriate.

Required:

- exact midnight callback
- exact 03:00 callback
- no midnight remote call
- fresh startup cache avoids remote call
- stale startup cache requests remote sync
- multi-day outage
- year boundary
- timezone configured by HA
- listener cancellation

## Done

Critical fail-safe scenario in TEST_PLAN.md passes.
