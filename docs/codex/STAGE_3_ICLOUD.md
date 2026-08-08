# Stage 3 — Apple iCloud CardDAV

## Goal

Implement the real v0.1 contact provider and authentication lifecycle.

## Required research first

Verify current iCloud CardDAV behavior and choose the smallest suitable maintained async-compatible dependency set.

Document dependency choice in a new ADR if it is architectural.

## Required work

- ICloudCardDAVProvider
- app-specific password login
- complete contact fetch
- minimal UID/FN/BDAY extraction
- source date representations
- connection/auth error taxonomy
- Config Flow validation
- duplicate account prevention
- ConfigEntryAuthFailed behavior
- reauth flow
- tests with mocked protocol responses

## Rules

Never request the primary Apple Account password.

Never persist raw vCards.

Never log complete contact payloads.

A partial address-book fetch must not become canonical.

## Manual smoke test

Document a privacy-safe procedure for testing against a real Apple account without committing any response payload.

## Done

A test iCloud account can sync birthdays, revoked credentials enter reauth, and temporary errors preserve cached normalized data.
