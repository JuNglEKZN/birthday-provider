# Apple iCloud Setup — user documentation baseline

v0.1 uses Apple iCloud Contacts through CardDAV.

## Prerequisite

The Apple Account must support and use two-factor authentication in order to generate an app-specific password.

## Create an app-specific password

1. Sign in to the Apple Account website.
2. Open **Sign-In and Security**.
3. Open **App-Specific Passwords**.
4. Generate a new app-specific password.
5. Give it a recognizable label such as `Home Assistant Birthday Provider`.
6. Copy the generated password.
7. In Home Assistant, add Birthday Provider and enter:
   - Apple Account
   - app-specific password

Do not enter the primary Apple Account password into Birthday Provider.

## Revocation

An app-specific password can be revoked independently from other app passwords.

If it is revoked, Birthday Provider should enter Home Assistant's reauthentication flow.

If the primary Apple Account password is changed or reset, Apple may revoke app-specific passwords; create a replacement and complete reauthentication.

## Privacy

Birthday Provider requests contacts from iCloud directly from the user's Home Assistant instance. There is no Birthday Provider relay server.
