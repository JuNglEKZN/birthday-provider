# Codex — Start Here

Use this file when beginning implementation.

## Repository state

Product and architecture planning are complete. Runtime implementation has not started.

## First Codex instruction

Paste the following into Codex:

> Work on Birthday Provider Stage 1 only.
>
> Read `SPECIFICATION.md`, `AGENTS.md`, all accepted ADRs, `docs/codex/MASTER_PROMPT.md`, and `docs/codex/STAGE_1_CORE.md` before editing anything.
>
> Treat `SPECIFICATION.md` as normative.
>
> Implement Stage 1 completely, run all relevant tests and checks, and stop after the Stage 1 completion report. Do not begin Stage 2.
>
> If you find an architectural contradiction or a material unknown that the specification does not resolve, stop and report it as a blocker instead of inventing a new design.

## After Stage 1

Do not simply ask Codex to "continue".

First:

1. Review Stage 1 completion report.
2. Review diff.
3. Confirm all tests pass.
4. Confirm no specification deviations.
5. Commit Stage 1.
6. Start a new branch/stage context for Stage 2.

Then use the same Master Prompt plus:

```text
docs/codex/STAGE_2_HA.md
```

Repeat for each stage.

## Stage mapping

| Stage | Prompt | Purpose |
|---|---|---|
| 1 | `STAGE_1_CORE.md` | Provider-neutral birthday logic |
| 2 | `STAGE_2_HA.md` | HA lifecycle with fixtures |
| 3 | `STAGE_3_ICLOUD.md` | Real iCloud CardDAV |
| 4 | `STAGE_4_SCHEDULING.md` | 00:00 / 03:00 and fail-safe |
| 5 | `STAGE_5_RELEASE.md` | Hardening and v0.1.0 |

## Do not allow Codex to

- add Google to v0.1
- add one sensor per person
- expose the full catalog as entity attributes
- change the active window
- change the Feb 29 policy
- use a drifting 24-hour interval in place of exact local schedules
- add telemetry
- store raw vCards
- add features from future stages
