# Test Plan

## Test philosophy

- Pure Core behavior is tested without Home Assistant.
- Home Assistant lifecycle is tested with mocked/fake providers.
- iCloud network behavior is tested with mocked protocol responses first.
- Real-account smoke testing is manual and never commits captured production data.

## Core test matrix

### Parsing

| Case | Expected |
|---|---|
| `1984-08-08` | year=1984, month=8, day=8 |
| `--08-08` | year=None, month=8, day=8 |
| invalid month | controlled invalid-contact result |
| invalid day | controlled invalid-contact result |
| missing UID | invalid contact |
| missing BDAY | contact ignored |

### Identity

- same name + different UID → two birthdays
- same UID + updated name → same identity, updated display value
- duplicate UID + identical payload → dedupe
- duplicate UID + conflicting payload → skip conflicting UID

### Leap-day

Reference coverage:

- leap year Feb 29
- non-leap year March 1
- Feb 28 → next day
- year boundary
- age for known year

### Active window

Include `days_until`: 0, 1, 2, 3.  
Exclude 4.

Boundaries:

- month end
- December → January
- leap-day scenarios
- multiple contacts same date

## Storage tests

- load absent snapshot
- load current schema
- corrupt snapshot handling
- save normalized-only fields
- no credentials in serialized data
- future migration test fixture reserved

## HA lifecycle tests

- Config Flow success
- cannot connect
- invalid auth
- duplicate config
- setup from cache
- setup without cache
- stale cache triggers startup refresh
- fresh cache suppresses startup refresh
- midnight recalculates active without remote fetch
- 03:00 invokes remote sync
- successful remote sync persists then updates runtime
- temporary sync failure retains cache/runtime
- auth failure triggers reauth
- reauth success updates credential
- unload cancels time listeners
- removal deletes specialized Store
- sensor state/attributes
- last-sync sensor
- diagnostics redaction / omission

## Critical fail-safe scenario

```text
Day 1 03:00 successful sync
→ normalized snapshot persisted
→ HA restarts
→ snapshot loads
→ iCloud unavailable
→ active window still calculated
→ 00:00 next day recalculates days_until
→ no remote data destruction
```

## Privacy regression tests

Assert absence of:

- password
- username from diagnostics
- names in diagnostics
- UIDs in diagnostics
- birthday dates in diagnostics
- phone/email/address in normalized models
- raw vCard in Store
