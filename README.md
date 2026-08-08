# Birthday Provider for Home Assistant

Birthday Provider is a privacy-first Home Assistant custom integration that reads birthdays from Apple iCloud Contacts and exposes a small, structured set of upcoming birthday events to Home Assistant.

## Status

**Planning complete. Implementation not started.**

The normative technical contract is in [`SPECIFICATION.md`](SPECIFICATION.md).  
The implementation sequence is in [`ROADMAP.md`](ROADMAP.md).  
Instructions for Codex and other coding agents are in [`AGENTS.md`](AGENTS.md) and [`docs/codex/`](docs/codex/).

Target first public release: **v0.1.0**

## v0.1 scope

Source:

- Apple iCloud Contacts
- CardDAV
- Apple Account + app-specific password

Output:

- one aggregated Home Assistant birthday sensor
- one last-successful-sync sensor
- active birthday events for today and the following 3 days
- age when a birth year exists
- `age: null` when only day/month exist

Rules:

- vCard UID is the stable identity
- February 29 is treated as March 1 in non-leap years
- remote iCloud sync runs daily at 03:00 in the Home Assistant local timezone
- the active window is recalculated locally at 00:00, at startup, and after successful remote sync
- a full normalized snapshot is stored locally so temporary iCloud outages do not break birthday logic

## Privacy

Birthday Provider runs inside the user's Home Assistant instance.

Contact data is fetched directly by Home Assistant from the configured contact provider. The project has:

- no project-operated backend
- no telemetry
- no analytics
- no external crash reporting
- no developer-controlled cloud API

The integration only needs:

- `UID`
- display name (`FN`)
- birthday (`BDAY`)

It must not persist phones, email addresses, postal addresses, notes, photos, organizations, or complete vCards.

Apple credentials remain in the user's Home Assistant Config Entry and must never be included in diagnostics or logs.

## Apple authentication

v0.1 uses an Apple **app-specific password**. The user's main Apple Account password must never be requested.

Two-factor authentication must be enabled on the Apple Account in order to create an app-specific password.

## Architecture

```text
Apple iCloud Contacts
        ↓ CardDAV
ICloudCardDAVProvider
        ↓
Provider-neutral Core
        ↓
Normalized persistent snapshot
        ↓
Active window: today → +3 days
        ↓
Home Assistant entities
        ├── automations
        ├── voice workflows
        └── e-ink consumers
```

The core is provider-neutral by design. Google Contacts is planned for **v0.2**, not v0.1.

## Planned Home Assistant entities

```text
sensor.birthday_provider
sensor.birthday_provider_last_sync
```

`sensor.birthday_provider` exposes only active events, not the entire address-book birthday catalog.

Example attributes:

```yaml
as_of: "2026-08-08"
window_days: 3
events:
  - id: "synthetic-contact-a"
    name: "Anna Petrova"
    date: "2026-08-08"
    days_until: 0
    age: 42
  - id: "synthetic-contact-b"
    name: "Sergey Ivanov"
    date: "2026-08-10"
    days_until: 2
    age: null
```

## Scheduling

Two independent processes are used:

```text
00:00 local HA time
→ recalculate active window from the local normalized snapshot

03:00 local HA time
→ synchronize iCloud Contacts
→ replace normalized snapshot only after a complete successful sync
→ recalculate active window
```

At startup:

- load the latest persistent normalized snapshot
- immediately calculate today's active window
- remote sync only if there is no snapshot or the last successful remote sync is older than 24 hours

## Installation

Not available yet. Implementation starts with Stage 1 in [`docs/codex/STAGE_1_CORE.md`](docs/codex/STAGE_1_CORE.md).

## Roadmap

- **v0.1** — Apple iCloud Contacts
- **v0.2** — Google Contacts via Google People API / OAuth2
- Later versions are intentionally not committed until the v0.1 architecture is validated

See [`ROADMAP.md`](ROADMAP.md).

## Security and privacy

See:

- [`SECURITY.md`](SECURITY.md)
- [`docs/PRIVACY.md`](docs/PRIVACY.md)
- [`docs/APPLE_SETUP.md`](docs/APPLE_SETUP.md)

## License

MIT. See [`LICENSE`](LICENSE).
