# Roadmap

This roadmap is deliberately staged to keep architectural decisions separate from implementation.

## Release strategy

- Specification and repository baseline: complete before coding
- v0.1.0: Apple iCloud production-ready MVP
- v0.2.0: Google Contacts provider
- No v0.3 commitment before v0.1 real-world validation

---

## Stage 0 — Repository and specification baseline

Status: **prepared**

Deliverables:

- SPECIFICATION.md
- README.md
- SECURITY.md
- PRIVACY.md
- ADRs
- test plan
- Codex instructions
- issue/PR templates
- HACS metadata
- validation workflows
- synthetic fixture policy

No runtime implementation.

Exit criterion: another developer can implement v0.1 without needing product clarification.

---

## Stage 1 — Provider-neutral Core

Goal: implement all birthday business logic with no Home Assistant dependency and no network calls.

Deliverables:

- canonical models
- ContactProvider protocol
- FixtureProvider
- BDAY parser
- normalizer
- occurrence calculation
- age calculation
- February 29 → March 1 policy
- active window 0–3
- duplicate UID policy
- deterministic sorting
- unit tests

Gate:

- no `homeassistant` imports under Core
- no CardDAV dependency required for Core unit tests
- all Stage 1 tests pass

Prompt: `docs/codex/STAGE_1_CORE.md`

---

## Stage 2 — Home Assistant skeleton

Goal: prove integration lifecycle using synthetic provider data.

Deliverables:

- manifest
- Config Flow skeleton
- Config Entry
- runtime data model
- persistent Store adapter
- coordinator/runtime orchestrator
- sensors
- privacy-safe diagnostics
- EN/RU translations
- unload/removal lifecycle
- HA tests using FixtureProvider

No real iCloud.

Gate:

- integration loads in HA test harness
- cache restore works
- sensors expose only active events
- diagnostics contain no PII

Prompt: `docs/codex/STAGE_2_HA.md`

---

## Stage 3 — Apple iCloud CardDAV

Goal: add real contact source.

Deliverables:

- ICloudCardDAVProvider
- app-specific password authentication
- complete address-book fetch
- iCloud/vCard interoperability handling
- temporary error mapping
- authentication failure mapping
- reauth flow
- integration tests with mocked CardDAV responses

Gate:

- no raw vCard persisted
- full snapshot completeness is enforceable
- revoked password enters reauth
- real test account validation documented

Prompt: `docs/codex/STAGE_3_ICLOUD.md`

---

## Stage 4 — Scheduling and fail-safe

Goal: deterministic calendar behavior and outage resilience.

Deliverables:

- local 00:00 active recalculation
- remote 03:00 sync
- startup freshness decision
- cached snapshot restore
- multi-day outage behavior
- listener cleanup
- scheduling tests

Gate scenario:

```text
successful remote sync
→ cache saved
→ HA restart
→ iCloud unavailable
→ active data recalculated correctly
→ next midnight recalculates active events from their occurrence dates
```

Prompt: `docs/codex/STAGE_4_SCHEDULING.md`

---

## Stage 5 — Hardening and public release

Goal: v0.1.0.

Deliverables:

- README installation instructions
- Apple setup walkthrough
- HACS validation
- Hassfest validation
- brand assets
- release workflow
- changelog
- real Home Assistant test
- privacy review
- security review
- manual acceptance checklist
- v0.1.0 GitHub Release

Gate:

- all Definition of Done items in SPECIFICATION.md pass
- no unresolved Major architecture issues
- no credentials or real contact data in git history

Prompt: `docs/codex/STAGE_5_RELEASE.md`

---

# v0.2 — Google Contacts

v0.2 begins only after v0.1 is stable.

Add:

- provider choice as first Config Flow step
- GoogleContactsProvider
- Google People API
- OAuth2 using Home Assistant-supported OAuth patterns
- provider-specific reauth
- one Config Entry per account/provider

Core birthday semantics remain unchanged.

The key architectural test for v0.2 is that adding Google does **not** require rewriting:

- Birthday
- ActiveBirthdayEvent
- occurrence calculation
- age
- February 29 handling
- active window
- sensor semantics

---

# Explicitly deferred

Not scheduled:

- calendar entity
- MQTT
- REST endpoint
- ICS export
- manual refresh service/button
- name morphology
- multiple-provider aggregation entity
- voice announcement generator
