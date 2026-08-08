# ADR 0002 — Home Assistant-native runtime

Status: Accepted

## Context

An earlier design used a separate Proxmox service that generated JSON for Home Assistant.

## Decision

v0.1 runs directly as a Home Assistant custom integration.

## Reasons

- HA is the primary consumer
- removes another runtime and network dependency
- native Config Flow / reauth / diagnostics
- simpler deployment
- e-ink and voice workflows already consume HA

## Trade-off

Birthday data is primarily available inside Home Assistant. Provider-neutral Core preserves future portability.
