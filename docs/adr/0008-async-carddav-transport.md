# ADR 0008 — Async CardDAV transport with constrained vCard extraction

Status: Accepted

## Decision

Stage 3 uses Home Assistant's injected `aiohttp` client session directly for
CardDAV discovery and `REPORT` requests. It adds no standalone CardDAV client
dependency.

The provider uses the RFC 6352 discovery sequence:

```text
current-user-principal
→ addressbook-home-set
→ address book collections
→ addressbook-query REPORT
```

The `REPORT` requests ask only for `UID`, `FN`, and `BDAY`. A deliberately
constrained vCard extractor unfolds and reads only those properties before
constructing `RawContact`; it never creates a full contact model or persists a
vCard.

## Consequences

- Network I/O remains asynchronous and uses Home Assistant's managed session.
- The integration has no additional transport requirement in its manifest.
- Any CardDAV collection or response that cannot be fetched completely fails
  the candidate sync rather than deleting data from the local snapshot.
- The extractor is intentionally not a general vCard API. Unsupported or
  malformed individual cards are skipped before the provider-neutral Core.
