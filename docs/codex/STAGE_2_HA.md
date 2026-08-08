# Stage 2 — Home Assistant Skeleton

## Goal

Implement Home Assistant lifecycle around FixtureProvider only.

## Prerequisite

Stage 1 completed with no specification deviations.

## Required work

- functional custom integration package
- manifest
- Config Flow skeleton using synthetic/provider fixture path only for tests
- Config Entry runtime structure
- Store abstraction and snapshot schema
- coordinator/orchestrator
- main aggregated sensor
- last-sync sensor
- diagnostics
- EN/RU translations
- unload
- remove-entry storage cleanup
- HA tests

## Important

Do not connect to iCloud yet.

Config Flow production fields may be scaffolded to match v0.1 UX, but validation uses an injected/mock provider.

Do not add `strings.json` as the custom integration localization source.

## Privacy tests

Diagnostics must not expose:

- username
- password
- UIDs
- names
- birthdays
- events

## Done

FixtureProvider-driven integration can load, restore cached data, expose active sensor state, unload cleanly, and pass diagnostics privacy tests.
