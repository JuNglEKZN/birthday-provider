# v0.1.0 Release Checklist

## Product

- [ ] v0.1 scope matches SPECIFICATION.md
- [ ] Google Contacts remains absent
- [ ] active window is 0–3 days
- [ ] Feb 29 policy is March 1
- [ ] no entity-per-contact behavior

## Privacy/security

- [ ] no real contacts in git history
- [ ] no credentials in git history
- [ ] diagnostics manually inspected
- [ ] logs manually inspected
- [ ] persistent snapshot inspected
- [ ] no telemetry/backend
- [ ] GitHub Private Vulnerability Reporting enabled

## Home Assistant

- [ ] Config Flow works
- [ ] reauth works
- [ ] startup from cache works
- [ ] midnight rollover works
- [ ] 03:00 local sync works
- [ ] unload removes listeners
- [ ] removal deletes Store
- [ ] EN and RU translations render correctly
- [ ] no `strings.json` dependency for custom integration translations

## Validation

- [ ] pytest passes
- [ ] Ruff/lint passes
- [ ] HACS action passes
- [ ] Hassfest passes
- [ ] supported HA version manual test passes

## HACS/public repository

- [ ] public GitHub repository
- [ ] repository description set
- [ ] topics set
- [ ] issues enabled
- [ ] `hacs.json` valid
- [ ] `manifest.json` documentation and issue_tracker URLs valid
- [ ] brand icon added
- [ ] README installation section updated
- [ ] changelog updated
- [ ] GitHub Release v0.1.0 created

## User acceptance

- [ ] known-year birthday
- [ ] no-year birthday
- [ ] multiple birthdays same day
- [ ] contact added after previous sync appears next day
- [ ] contact changed
- [ ] contact removed
- [ ] revoked app password produces reauth
- [ ] iCloud outage preserves working active data
