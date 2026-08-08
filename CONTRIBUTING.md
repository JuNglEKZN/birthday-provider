# Contributing

## Before opening a PR

Read:

- `SPECIFICATION.md`
- `AGENTS.md`
- relevant ADRs
- `ROADMAP.md`

## Scope

Keep PRs stage-scoped and small enough to review.

Do not combine architectural changes with feature implementation.

## Privacy

All fixtures, screenshots, and logs must be synthetic.

Never commit:

- real Apple Account identifiers
- app-specific passwords
- real contact names
- real birthdays
- real vCard UIDs
- exported address books

## Architecture changes

If a proposed change alters a normative decision, add an ADR under `docs/adr/` and get that ADR accepted before implementation.

## Tests

Every behavioral change requires tests.

## Home Assistant compatibility

Use current Home Assistant custom-integration patterns. The project aims to stay aligned with modern Config Flow, Config Entry, diagnostics, localization, and async practices.

## Pull requests

Use the provided PR template and explicitly state whether the PR changes any normative specification.
