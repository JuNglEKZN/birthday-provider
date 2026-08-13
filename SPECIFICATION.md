# Birthday Provider for Home Assistant
## Technical Specification v1.0 — implementation baseline

Status: **Normative**

This document is the implementation contract for v0.1.0. If code, README text, issue descriptions, or agent prompts conflict with this document, this document wins unless an ADR explicitly changes the decision.

---

## 1. Purpose

Birthday Provider is a Home Assistant custom integration that retrieves birthdays from Apple iCloud Contacts through CardDAV, normalizes them, persists the minimum required dataset locally, calculates birthday occurrences, and exposes active birthday events to Home Assistant.

Primary consumers:

- Home Assistant automations
- voice announcement workflows
- e-ink data consumers
- dashboards and templates

The integration does not implement voice text, e-ink layout, calendar UI, address-book editing, or notifications.

---

## 2. v0.1 target architecture

```text
Apple / iCloud Contacts
        ↓
      CardDAV
        ↓
ICloudCardDAVProvider
        ↓
ContactProvider contract
        ↓
Provider-neutral Core
        ↓
Normalized Birthday[]
        ↓
Home Assistant persistent Store
        ↓
Active window calculation
        ↓
BirthdayProviderCoordinator/runtime data
        ↓
Aggregated HA sensors
```

There is no external Birthday Provider server.

---

## 3. Public project / privacy model

The repository is public.

Runtime credentials and contact data belong to each user's Home Assistant instance.

The project must not operate:

- backend infrastructure
- telemetry
- analytics
- developer-controlled cloud APIs
- external crash reporting
- synchronization relays

User data flow is only:

```text
User Home Assistant ↔ Apple iCloud
```

The integration must never intentionally transmit contact data to the project author.

---

## 4. Scope: v0.1

v0.1 must provide:

- Home Assistant custom integration
- UI Config Flow
- iCloud Contacts via CardDAV
- Apple Account identifier + app-specific password
- reauthentication
- full remote sync once per day
- normalized local persistent snapshot
- birthdays with and without year
- stable identity from vCard UID
- February 29 policy
- active window: today through +3 calendar days
- multiple birthdays on the same date
- deterministic sorting
- safe diagnostics
- local fail-safe operation during temporary iCloud outage
- English and Russian custom-integration translations
- HACS-compatible repository layout
- test suite

---

## 5. Explicitly out of scope: v0.1

Do not implement:

- Google Contacts
- provider selector in Config Flow
- REST API
- MQTT
- ICS export
- calendar entity
- one entity per contact
- manual refresh button/action
- YAML configuration
- name declension / morphology
- Alice/Yandex logic
- e-ink rendering
- address-book editing
- write-back to iCloud
- phone/email/address ingestion
- project backend
- telemetry

Google Contacts is reserved for v0.2.

---

## 6. Provider-neutral architecture

Core logic must not be designed around iCloud-specific classes or CardDAV-specific payloads.

Contract:

```python
class ContactProvider(Protocol):
    async def async_fetch_contacts(self) -> list[RawContact]:
        ...
```

v0.1 implementation:

```text
ICloudCardDAVProvider
```

Future v0.2 implementation:

```text
GoogleContactsProvider
```

The following must remain provider-neutral:

- Birthday model
- active-event model
- date normalization
- age calculation
- February 29 handling
- occurrence calculation
- sorting
- Home Assistant entity semantics

---

## 7. Data minimization

From a source contact, the integration may retain only:

- UID
- display name / FN
- BDAY

The integration must not persist:

- phone numbers
- email addresses
- postal addresses
- notes
- organizations
- job titles
- contact images
- URLs
- social profiles
- raw/complete vCards

The parser may temporarily see raw vCard data while processing but must reduce it immediately to the minimal RawContact form.

---

## 8. Canonical models

### 8.1 RawContact

Provider output conceptually contains:

```python
RawContact:
    uid: str
    display_name: str
    birthday_raw: str | parsed birthday value
```

No unrelated address-book data belongs in this model.

### 8.2 Birthday

```python
Birthday:
    id: str
    name: str
    day: int
    month: int
    year: int | None
```

Requirements:

- immutable where practical
- serializable to JSON-compatible storage representation
- validated day/month/year
- ID is vCard UID in v0.1

### 8.3 ActiveBirthdayEvent

```python
ActiveBirthdayEvent:
    id: str
    name: str
    date: date
    age: int | None
```

`ActiveBirthdayEvent` contains no relative-day field. Consumers that need an
offset may derive `event.date - as_of` locally.

---

## 9. Stable identity

The vCard UID is the canonical contact identity.

Display name must not be used as identity.

Required behavior:

- identical names with different UIDs are separate contacts
- renaming a contact does not change identity
- changing BDAY updates the same identity
- deletion is detected only from a complete successful full snapshot

---

## 10. BDAY parsing

At minimum support:

```text
YYYY-MM-DD
--MM-DD
```

Also support equivalent parsed values emitted by the selected standards-compliant vCard library if required for iCloud interoperability.

Normalization result:

```text
day
month
year | None
```

Forbidden placeholder years:

```text
0000
1900
1970
```

A missing source year must remain `None`.

---

## 11. Missing year

Example:

```text
--08-17
```

Normalizes to:

```text
day = 17
month = 8
year = None
```

Age must be `None`.

The integration must never infer, estimate, or fabricate a birth year.

---

## 12. Age

Age is calculated for the concrete birthday occurrence.

When year is known:

```text
age = occurrence_year - birth_year
```

When year is unknown:

```text
age = None
```

---

## 13. February 29 policy

Normative project rule:

```text
February 29 → March 1 in non-leap years
```

Examples:

```text
2028 → 2028-02-29
2029 → 2029-03-01
2030 → 2030-03-01
```

This exact policy applies to:

- occurrence date
- active-window inclusion
- age

---

## 14. Active window

An occurrence is active when:

```text
as_of <= event.date <= as_of + 3 calendar days
```

The event date is concrete; no relative-day field is stored or exposed.

No cap exists on the number of birthday events on one date.

---

## 15. Sorting

Canonical normalized birthdays:

```text
month ASC
day ASC
name casefold ASC
id ASC
```

Active events:

```text
date ASC
name casefold ASC
id ASC
```

Output must be deterministic.

---

## 16. Scheduling: two independent clocks

### 16.1 Local active recalculation

Run:

- at integration startup
- at each local calendar rollover, 00:00 Home Assistant local time
- after every successful remote sync

No iCloud connection is required.

### 16.2 Remote iCloud synchronization

Run once per calendar day at:

```text
03:00 Home Assistant local time
```

At startup, perform an extra remote sync only when:

- no persistent normalized snapshot exists; or
- `last_successful_sync` is older than 24 hours

A Home Assistant restart by itself must not cause an unnecessary iCloud request when the cached snapshot is fresh.

Use Home Assistant event/time helpers suitable for exact local-time scheduling. The implementation must retain and call unsubscribe callbacks on unload.

---

## 17. Persistent snapshot

Persist the full normalized Birthday dataset, not a precomputed active event list.

Conceptual structure:

```json
{
  "schema_version": 1,
  "generated_at": "2026-08-08T03:00:00+03:00",
  "birthdays": [
    {
      "id": "synthetic-a",
      "name": "Anna Petrova",
      "day": 8,
      "month": 8,
      "year": 1984
    }
  ]
}
```

Do not persist:

- credentials
- raw vCards
- phones
- email addresses
- addresses
- a precomputed active-event list as the source of truth

Use Home Assistant's Store helper.

---

## 18. Startup behavior

On config entry setup:

1. Load the persistent normalized snapshot if present.
2. Calculate active events immediately for the current HA-local date.
3. Make cached data available to entities if valid.
4. Decide whether startup remote refresh is required using the 24-hour freshness rule.
5. Register midnight and 03:00 schedules.

If no snapshot exists and initial remote fetch cannot complete, the integration must remain unavailable / retry appropriately rather than fabricate an empty successful dataset.

---

## 19. Remote sync transactional rule

A remote sync is canonical only after the entire pipeline succeeds:

```text
authenticate
→ fetch complete address book
→ parse
→ normalize
→ validate
→ resolve duplicates
→ sort
→ persist new snapshot
→ replace runtime canonical data
→ recalculate active events
```

If completeness cannot be guaranteed, the old canonical snapshot must remain unchanged.

---

## 20. Error taxonomy

### Authentication failure

Examples:

- revoked app-specific password
- invalid app-specific password

Behavior:

- raise / propagate Home Assistant authentication failure in a way that starts reauthentication
- do not delete cached normalized birthday data

### Temporary communication failure

Examples:

- timeout
- transient network error
- iCloud temporary failure

Behavior:

- retain last successful normalized snapshot
- retain `last_successful_sync`
- continue local active calculations
- mark/report remote update failure

### Malformed individual contact

Behavior:

- skip that contact
- warning/debug diagnostic metadata may reference UID, not sensitive fields
- continue processing other contacts

### Incomplete remote snapshot

Behavior:

- treat full synchronization as failed
- do not delete contacts based on partial data
- do not replace persistent snapshot

---

## 21. Duplicate UID

Canonical dataset must contain unique IDs.

v0.1 deterministic policy:

- if duplicate UID records normalize to exactly identical Birthday values, deduplicate to one record
- if duplicate UID records conflict, skip that UID entirely from the new candidate dataset and record a warning
- the overall sync may continue if the rest of the dataset is known complete

This behavior must be tested.

---

## 22. Contact deletion

A previously cached birthday is removed only when a subsequent **complete successful remote snapshot** no longer contains that UID.

A failed/incomplete remote sync must never trigger deletions.

---

## 23. Config Flow

v0.1 flow goes directly to Apple iCloud setup.

Do not present a provider selector in v0.1.

Fields:

- Apple Account
- app-specific password

The flow must test credentials / connectivity before creating the Config Entry.

The integration must prevent accidental duplicate setup of the same Apple account where practical, but duplicate protection must not expose account identifiers in logs/diagnostics.

---

## 24. Apple authentication

Use an Apple app-specific password.

The integration must never request the user's primary Apple Account password.

README/setup docs must explain:

- two-factor authentication is required to generate an app-specific password
- the app-specific password can be revoked independently
- changing/resetting the main Apple Account password may revoke app-specific passwords and require reauthentication

---

## 25. Reauthentication

When previously valid credentials stop working:

- Home Assistant must start a reauth flow
- the user can replace the app-specific password
- persistent normalized birthday data is preserved
- successful reauth resumes normal sync without recreating the integration

---

## 26. Home Assistant runtime design

Recommended runtime concept:

```python
BirthdayProviderRuntimeData:
    coordinator
    storage
    provider
    unsubscribe_callbacks
```

Use modern Config Entry runtime data rather than broad global `hass.data` dictionaries where practical for the supported Home Assistant baseline.

---

## 27. Entities

v0.1 creates no entity per contact.

### 27.1 `sensor.birthday_provider`

State:

```text
count of active events (0–3 days)
```

Attributes:

```yaml
as_of: "2026-08-08"
window_days: 3
events:
  - id: "synthetic-a"
    name: "Anna Petrova"
    date: "2026-08-08"
    age: 42
```

Only active events are exposed.

The full normalized catalog stays internal.

### 27.2 `sensor.birthday_provider_last_sync`

State:

```text
timestamp of the last successful remote iCloud sync
```

Failed remote sync does not advance the timestamp.

---

## 28. Recorder / privacy boundary

Do not expose the entire birthday catalog in HA state attributes.

Only the short active 0–3 day window may be placed in entity attributes.

Reasons:

- Recorder database growth
- privacy minimization
- state payload size

---

## 29. Diagnostics

Implement config-entry diagnostics.

Diagnostics may include:

- integration version
- provider type
- normalized birthday count
- active-event count
- last successful remote sync
- last remote sync status/category
- HA timezone
- snapshot schema version

Diagnostics must not include:

- Apple Account
- password
- contact UIDs
- names
- birthday dates
- event objects
- raw vCards

Diagnostics must be safe for a user to attach to a public GitHub issue.

---

## 30. Logging

Allowed:

```text
Birthday sync started
Contacts fetched: 152
Birthdays normalized: 41
Active events: 3
Birthday sync completed
```

Forbidden:

- passwords
- Apple Account
- raw vCard
- phone
- email
- postal address
- notes

Prefer UID only for internal warning correlation if necessary; diagnostics still must not include UIDs.

---

## 31. Localization

This is a custom integration.

Use:

```text
custom_components/birthday_provider/translations/en.json
custom_components/birthday_provider/translations/ru.json
```

Do **not** rely on `strings.json` for custom-integration runtime localization.

English and Russian must cover:

- Config Flow labels
- descriptions
- errors
- abort reasons
- reauth text
- entity names if translation keys are used

---

## 32. Manifest / repository

Domain:

```text
birthday_provider
```

Manifest must include at least:

- domain
- name
- version
- documentation
- issue_tracker
- codeowners
- config_flow
- integration_type
- iot_class
- requirements

Recommended:

```text
integration_type = service
iot_class = cloud_polling
```

The custom integration version uses Semantic Versioning.

---

## 33. HACS

Repository contains exactly one integration under:

```text
custom_components/birthday_provider/
```

The repository must include:

- `hacs.json`
- public GitHub repository metadata
- HACS validation workflow
- Hassfest validation workflow
- brand assets before HACS default submission
- a real GitHub Release for HACS default submission

Brand image design is not part of programming stages but is a release gate.

---

## 34. Testing

Tests must be synthetic only.

Never commit production contact data.

Required categories:

- BDAY parsing with year
- BDAY parsing without year
- malformed BDAY
- UID missing
- duplicate identical UID
- duplicate conflicting UID
- same name / different UID
- age known/unknown
- leap-year policy
- active days 0,1,2,3 included
- day 4 excluded
- month boundary
- year boundary
- several birthdays same date
- deterministic sorting
- snapshot serialization/migration
- startup from cache
- startup stale/no cache
- midnight rollover
- 03:00 sync trigger
- temporary outage
- authentication failure and reauth
- diagnostics privacy
- log privacy
- removal cleanup

---

## 35. Removal

When a Config Entry is deleted:

- remove integration-specific persistent birthday snapshot
- unregister schedules/listeners
- unload sensor platforms
- allow Home Assistant to remove Config Entry credentials

---

## 36. v0.2 roadmap contract

v0.2 adds Google Contacts.

Expected provider:

```text
GoogleContactsProvider
```

Expected source API:

```text
Google People API
```

Expected auth:

```text
OAuth2
```

v0.1 must not include unfinished Google UI or provider-selection UI.

However, v0.1 core and entity semantics must not require modification when Google is later added.

---

## 37. Project boundaries

Birthday Provider is:

```text
Contacts → Birthday normalization → Home Assistant birthday data
```

Birthday Provider is not:

- address-book manager
- calendar application
- notification engine
- voice-assistant integration
- e-ink renderer
- cloud service

---

## 38. Definition of Done: v0.1.0

A user can:

1. install the integration
2. add it through HA UI
3. enter Apple Account and app-specific password
4. retrieve birthdays from iCloud Contacts
5. add/change/remove a birthday in Contacts and see it after the next successful daily sync
6. use birthdays today through +3 days
7. receive age when year exists
8. receive no fabricated age when year is missing
9. handle multiple birthdays on one date
10. handle February 29 under the March 1 policy
11. restart HA and immediately use cached normalized data
12. survive temporary iCloud outage while recalculating active events locally
    from the cached normalized catalog
13. replace a revoked app-specific password through reauth
14. download privacy-safe diagnostics
15. remove the integration and its specialized snapshot
16. install/update the public release through HACS custom repository flow

All tests and repository validation workflows pass.
