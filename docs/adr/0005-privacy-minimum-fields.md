# ADR 0005 — Minimum contact fields

Status: Accepted

## Decision

Retain only:

- UID
- FN/display name
- BDAY

## Consequence

Complete vCards and unrelated contact properties are discarded after parsing and never persisted or included in diagnostics.
