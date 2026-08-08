# AGENTS.md — Coding Agent Contract

This repository is specification-driven.

## Authority order

1. `SPECIFICATION.md`
2. Accepted ADRs under `docs/adr/`
3. Current stage prompt under `docs/codex/`
4. `ROADMAP.md`
5. README and other explanatory documentation

If these conflict, stop and report the conflict. Do not silently choose a new architecture.

## Global rules

- Work only on the requested stage.
- Do not implement future-stage functionality “because it is easy”.
- Keep Core independent of Home Assistant.
- Never commit real credentials or real contact data.
- Never add telemetry, analytics, project backend, or external reporting.
- Do not persist complete vCards.
- Treat UID, display name, and BDAY as the maximum retained contact dataset.
- Do not create one HA entity per contact.
- Do not add Google Contacts before v0.2.
- Do not add provider-selection UI in v0.1.
- Do not change the February 29 policy.
- Do not change the active window from 0–3 days.
- Do not replace exact local schedules with a drifting “every 24 hours” timer.
- Do not use `strings.json` as the custom-integration localization source. Use `translations/*.json`.
- Preserve privacy-safe diagnostics.
- Use synthetic test data only.

## Stage discipline

Before coding:

1. Read `SPECIFICATION.md` completely.
2. Read the assigned stage prompt completely.
3. Inspect relevant existing code/tests.
4. State any normative conflict before editing.

After coding:

1. Run the stage test suite.
2. Run repository validation/linting available for that stage.
3. Check `git diff`.
4. Confirm no secrets or real personal data were added.
5. Report exactly:
   - implemented
   - tests run and results
   - deviations from specification
   - blockers
   - files changed

## Change control

Any change to these decisions requires a new ADR before implementation:

- provider-neutral Core
- v0.1 Apple-only scope
- 00:00 local active recalculation
- 03:00 local iCloud remote sync
- active window 0–3 days
- February 29 → March 1
- vCard UID identity
- privacy field set UID/FN/BDAY
- full normalized snapshot rather than active-only cache
- no entity per contact
- public/no-backend privacy model

## Security

Never print or log:

- app-specific password
- primary Apple password
- full vCards
- phone numbers
- email addresses
- postal addresses
- contact notes

Diagnostics must not contain:

- Apple Account
- UID
- names
- birthday dates
- event lists
- credentials

## Codex stop conditions

Stop instead of guessing if:

- CardDAV completeness cannot be established
- iCloud returns a birthday representation not covered by tests/spec
- Home Assistant API changes materially invalidate the prescribed lifecycle
- a dependency would require storing more contact data
- a stage needs a decision owned by a future stage

Produce a blocker report with options instead of bypassing the specification.
