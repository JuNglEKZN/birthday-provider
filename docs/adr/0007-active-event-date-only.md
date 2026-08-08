# ADR 0007 — Active events use occurrence date, not `days_until`

Status: Accepted

## Context

The complete normalized birthday dataset is already persisted locally in Home Assistant.

For the current active view, every birthday occurrence has a concrete calendar `date`. A separate `days_until` field duplicates information that can be derived from:

```text
event.date
-
as_of
```

Keeping both values creates two representations of the same fact and introduces a risk of inconsistency.

## Decision

`ActiveBirthdayEvent` contains:

```python
ActiveBirthdayEvent:
    id: str
    name: str
    date: date
    age: int | None
```

It does not contain `days_until`.

The active window is selected directly by date:

```text
as_of <= event.date <= as_of + 3 calendar days
```

"Birthday today" is determined by:

```text
event.date == as_of
```

Consumers that need a relative offset may calculate it from the two dates locally.

## Consequences

- persistent Birthday data remains only `id`, `name`, `day`, `month`, `year`
- no relative-day counter is persisted
- no relative-day counter is exposed in the v0.1 active-event contract
- midnight recalculation updates the active event set based on calendar dates
- Home Assistant, voice, and e-ink consumers use `date`/`as_of` rather than `days_until`
