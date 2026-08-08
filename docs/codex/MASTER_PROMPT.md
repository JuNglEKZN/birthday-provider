# Codex Master Prompt

You are implementing **Birthday Provider for Home Assistant**.

The repository is specification-driven.

Before changing code:

1. Read `SPECIFICATION.md` fully.
2. Read `AGENTS.md` fully.
3. Read every accepted ADR relevant to your assigned stage.
4. Read the assigned stage file under `docs/codex/`.
5. Inspect current tests and implementation.
6. Do not begin a future stage.

Normative authority:

```text
SPECIFICATION.md
> accepted ADRs
> assigned stage prompt
> ROADMAP.md
> explanatory docs
```

Do not redesign the project unless a normative contradiction blocks implementation.

Critical fixed decisions:

- v0.1 is Apple iCloud only.
- Core is provider-neutral.
- v0.2 adds Google, not v0.1.
- only UID/FN/BDAY are retained.
- vCard UID is identity.
- Feb 29 → March 1 in non-leap years.
- active window is 0–3 days.
- full normalized dataset is persisted.
- active data is recalculated locally.
- 00:00 local: active recalculation.
- 03:00 local: iCloud sync.
- no project backend/telemetry.
- no entity per contact.
- custom-integration localization uses `translations/*.json`, not runtime dependence on `strings.json`.

Security:

- use only synthetic contact fixtures
- never output or commit production credentials
- never log a password or raw vCard
- diagnostics must be safe to attach to a public GitHub issue

At the end of every stage return:

## Implemented
Exact components completed.

## Tests
Commands run and exact results.

## Specification deviations
Write `None` if none.

## Blockers
Only genuine blockers.

## Files changed
List files.

Do not continue into the next stage automatically.
