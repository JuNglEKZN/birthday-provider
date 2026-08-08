# Stage 1 — Provider-neutral Core

## Goal

Implement all birthday-domain behavior without Home Assistant imports and without network access.

## Required work

Implement:

- canonical immutable models
- `RawContact`
- `ContactProvider` protocol/ABC
- `FixtureProvider`
- BDAY parsing for year and no-year forms
- normalization to Birthday
- validation
- UID identity
- duplicate UID policy from specification
- occurrence calculation
- age
- Feb 29 → Mar 1
- active window 0–3
- deterministic sorting
- unit tests

## Constraints

No imports from `homeassistant`.

No real CardDAV.

No Google.

No Config Flow.

No scheduling.

No persistent HA Store.

No sensors.

Use pure functions for calendar calculations and pass reference dates explicitly.

## Suggested files

```text
custom_components/birthday_provider/core/
  __init__.py
  models.py
  provider.py
  parsing.py
  birthdays.py

tests/
  test_core_models.py
  test_core_parsing.py
  test_core_occurrence.py
  test_core_active.py
  test_core_duplicates.py
  fixtures/
```

## Required test cases

- YYYY-MM-DD
- --MM-DD
- invalid month/day
- missing UID
- same name / different UID
- duplicate identical UID
- duplicate conflicting UID
- known age
- unknown age
- leap and non-leap Feb 29
- days 0/1/2/3 included
- day 4 excluded
- month/year boundary
- multiple birthdays same day
- deterministic order
- unrelated contact fields never enter normalized model

## Stop conditions

Stop if a parser dependency is required and choosing it materially constrains Stage 3 CardDAV behavior. Present options instead of selecting blindly.

## Done

All Stage 1 tests pass and Core contains no HA/network dependency.
