# Privacy Design

## Principle

Birthday Provider is local software that talks directly from Home Assistant to the configured contacts provider.

For v0.1:

```text
Home Assistant ↔ Apple iCloud CardDAV
```

There is no Birthday Provider cloud service.

## Minimum retained contact data

Only:

- UID
- display name
- birthday

## Data deliberately not retained

- phones
- emails
- addresses
- notes
- photos
- organizations
- titles
- URLs
- raw vCards

## Home Assistant state boundary

The full normalized birthday catalog is private internal storage.

Only active events for the 0–3 day window may be exposed as sensor attributes.

## Diagnostics boundary

Diagnostics must contain aggregate metadata only.

Allowed examples:

- normalized birthday count
- active event count
- provider type
- last sync timestamp
- last sync result category
- timezone
- snapshot schema version

Forbidden:

- Apple Account
- credentials
- UID
- contact names
- dates of birth
- active event list

## GitHub boundary

All examples and fixtures are synthetic.

No production diagnostic dump, screenshot, exported vCard, or contact fixture may be committed without manual privacy review.
