# ADR 0001 — Provider-neutral Core

Status: Accepted

## Decision

Birthday business logic is provider-neutral.

v0.1 implements `ICloudCardDAVProvider`. Google Contacts is a v0.2 provider.

## Consequences

No iCloud/CardDAV-specific types are permitted in canonical Birthday or ActiveBirthdayEvent models.

Adding Google must not require changing birthday calculation semantics.
