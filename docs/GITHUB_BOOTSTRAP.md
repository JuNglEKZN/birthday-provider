# GitHub Bootstrap — exact commands

Target repository:

```text
https://github.com/JuNglEKZN/birthday-provider
```

Run these commands from the directory that contains the prepared `birthday-provider` folder.

## Option A — GitHub CLI

```bash
cd birthday-provider

git init
git branch -M main
git add .
git commit -m "chore: bootstrap Birthday Provider specification and repository"

gh auth login
gh repo create JuNglEKZN/birthday-provider \
  --public \
  --source=. \
  --remote=origin \
  --push \
  --description="Privacy-first Home Assistant integration for birthdays from iCloud Contacts."
```

Then configure topics:

```bash
gh repo edit JuNglEKZN/birthday-provider \
  --add-topic home-assistant \
  --add-topic homeassistant \
  --add-topic hacs \
  --add-topic icloud \
  --add-topic carddav \
  --add-topic contacts \
  --add-topic birthdays \
  --add-topic python
```

## Option B — GitHub web

1. Create a new public repository named `birthday-provider`.
2. Do not initialize it with README, .gitignore, or license.
3. Locally run:

```bash
cd birthday-provider

git init
git branch -M main
git add .
git commit -m "chore: bootstrap Birthday Provider specification and repository"

git remote add origin git@github.com:JuNglEKZN/birthday-provider.git
git push -u origin main
```

## After push

GitHub repository settings:

- Issues: ON
- Discussions: optional
- Wiki: OFF
- Squash merge: ON
- Delete head branches after merge: ON

Before v0.1.0:

- enable Private Vulnerability Reporting
- protect `main`
- require CI status checks
- add final brand icon
- create a real GitHub Release

## First development branch

```bash
git checkout -b stage-1/core
```

Open Codex and follow `CODEX_START_HERE.md`.
