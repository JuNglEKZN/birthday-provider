# GitHub Repository Setup

Target repository:

```text
JuNglEKZN/birthday-provider
```

Recommended GitHub description:

```text
Privacy-first Home Assistant integration for birthdays from iCloud Contacts.
```

Recommended topics:

```text
home-assistant
homeassistant
hacs
icloud
carddav
contacts
birthdays
python
```

## Repository settings

- Visibility: Public
- Default branch: `main`
- Issues: enabled
- Discussions: optional
- Wiki: disabled unless actively used
- Squash merge: enabled
- Automatically delete head branches: enabled
- Private vulnerability reporting: enable before v0.1.0

## Branch protection after initial bootstrap

Protect `main`:

- require pull request before merging
- require status checks:
  - HACS validation
  - Hassfest
  - tests
- require branch to be up to date
- block force pushes
- block branch deletion

For solo development, required approvals can remain 0/disabled while still requiring CI.

## Initial commit

Suggested:

```text
chore: bootstrap Birthday Provider specification and repository
```

No production integration behavior should be included in the bootstrap commit beyond repository metadata/translation placeholders.

## First coding branch

```text
stage-1/core
```

Run Codex with:

```text
docs/codex/MASTER_PROMPT.md
+
docs/codex/STAGE_1_CORE.md
```
