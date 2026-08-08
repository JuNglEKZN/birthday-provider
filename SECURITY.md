# Security Policy

## Supported versions

Until v1.0, only the latest published release is expected to receive security fixes.

## Reporting a vulnerability

Do not publish credentials, contact data, or reproducible secrets in a public issue.

For early development, open a GitHub issue containing no sensitive payload and clearly mark it as a security concern. Before the first public release, configure GitHub Private Vulnerability Reporting and update this file to direct reporters there.

## Credential model

Birthday Provider v0.1 uses an Apple app-specific password.

The integration must never request the user's primary Apple Account password.

Credentials are stored in the user's Home Assistant Config Entry and are not part of this repository.

## Data access

The integration is designed to retain only:

- vCard UID
- contact display name
- birthday

Other contact fields must be discarded and must not be persisted.

## No project backend

This project operates no server that receives user contact data or Apple credentials.

## Diagnostics

Diagnostics are designed for public issue attachment and therefore must exclude personal contact information and credentials.

## Logging

Production logging must not contain credentials or complete vCards.

## Dependency policy

Third-party Python dependencies should be minimized, pinned in the Home Assistant manifest where required, and reviewed for blocking I/O and unexpected network/telemetry behavior before adoption.
