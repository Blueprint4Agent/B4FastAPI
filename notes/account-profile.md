# Personal profile and account security

[Korean](ko/account-profile.md)

Issue #92 separates the standalone `/profile` page from Account settings.
The sidebar profile dropdown and Account Go to profile action open it inside the
existing AppShell, preserving sidebar width and expansion. It is private to the signed-in account; there is no public
profile URL or arbitrary-user profile lookup.

Profile owns name, managed photo, optional Bio (100 characters), optional country/region and read-only signup date. Country and city/region are chosen from linked dropdowns, never geolocation. Account owns current name (inline editing), email, connected sign-in providers, signup date, password
change and deletion. Its profile action opens the standalone profile page.

GET/PATCH `/api/v1/auth/me` remains the source of truth. Bio is trimmed; blank/null clears it and omission preserves it. Location is a
validated country:region catalog ID; null clears it and omission preserves it. Signup date, role and credential
availability cannot be edited. `has_password` only indicates whether an existing
email credential can be changed. No credential hashes or storage keys are exposed.
Apply migration `0016_personal_profile` with `make db-migrate` before rollout.
The managed photo endpoints and storage policy are unchanged.

## Password change

A bearer session requests POST `/api/v1/auth/me/password/code`. The service sends a
six-digit code only to that account's registered email through the existing Celery
mail task (`password_change`). POST `/api/v1/auth/me/password` accepts `{code, password}`.
The new password uses the existing signup/reset strength policy. OAuth-only accounts
manage passwords with their provider; this endpoint never creates email credentials.
API keys alone cannot authorize either operation.

The shared account-deletion challenge implementation retains separate Redis keys
and HMAC domains for each purpose. Codes expire after ten minutes, are single-use,
and only the latest issued code is valid. Issuance is limited to once per 30 seconds and
five times per hour. Five incorrect attempts lock verification/issuance for the
remaining ten-minute attempt window; resend does not reset it. Concurrent consumers
cannot both succeed. Cache/queue failures fail closed. A consumed code must be
reissued after a database failure. Credential replacement uses compare-and-swap.

Refresh sessions are revoked before the credential commit. Existing access tokens
remain valid until their normal expiry; API keys are unchanged. The current browser
also signs in again on its next required refresh. Revocation and DB replacement are
not a distributed transaction: a failure may revoke sessions without changing the
password. The UI reports failure and requires another code rather than claiming success.

`EMAIL_ENABLED=false` rejects code issuance, password changes, forgot/reset password,
and deletion, including previously issued proofs. UI explains the restriction and
disables the affected actions; it never bypasses email proof. Profile edits and normal
login remain available. Mail queue acceptance is not proof of SMTP delivery. Restart
API/workers with matching versions when adding the new mail kind.

## State and recovery

AuthProvider owns the confirmed profile and updates the sidebar from successful
mutations. Form drafts stay local, errors retain the saved snapshot, and account
switches reset drafts. Profile editing uses a modal with photo preview and the
existing Add photo/Remove photo controls at the top. Photo edits save immediately;
Save confirms name/Bio/location. Outside the modal the avatar reveals an edit icon
on hover/focus; touch devices keep it visible. Password entry lives only in a modal. Reload/login and existing desktop recovery refresh the owner.
No new polling, global store or realtime profile events are added; other open clients
see changes on their next existing refresh/reload.


Location options use a pinned MIT country-region-data snapshot (249 countries,
4,387 subdivisions), not an exhaustive world-city database. Country names use
Intl.DisplayNames; Korean regions have native Korean labels. Country changes clear
the region draft, and Save requires a valid pair or no location. Where upstream
shortcodes are absent, stable internal hashed IDs are used. Backend validates the
same adopted pairs. Source and license:
https://github.com/country-regions/country-region-data/tree/e65e124da5e846a833eba68e228b6d50aad42817

Both Account and Profile show the current plan from the existing account-owned
subscription snapshot, with unknown/error and retry states. Billing-disabled
instances display Free and no management action. Navigation does not create a
second subscription cache or trigger a fresh read for a confirmed snapshot.

Bio is limited to 100 Unicode code points on both client and API. The editor shows n/100; the profile body preserves line breaks and grows naturally without truncation. Photo add/remove use the shared rectangular Button.

Name, Bio and location can also be edited in place on Profile. Name has a stable minimum width independent of spaces; Bio starts with a 96px
three-line editing area and scrolls internally. Save/cancel use backgroundless icons. Location opens
an anchored popover without expanding the metadata strip. Each inline save patches
only that field, and failed writes retain the draft. Account name editing uses the
same AuthProvider mutation path. Password and deletion share AccountEmailVerification
for recipient, code/send row and lifetime hint, plus the same compact Modal frame.


Code flow is request → verify → change/delete. Resend is available after 30 seconds; only the latest code is valid for 10 minutes. Checking never extends expiry; final actions revalidate and consume. Code feedback appears beneath its input. Password and confirmation share signup validation UI. Profile navigation preserves the source Settings/Admin/main sidebar family in route history state, including reload.

Profile shortcut defaults to Cmd+Shift+P on macOS and Ctrl+Shift+P elsewhere, is customizable in Keyboard settings, and ignores text editing and open dialogs. Existing two-action shortcut records remain accepted. The showcase includes shared backgroundless pencil/check/close icon buttons.

Profile enters with the existing 260ms rise animation and honors the global reduced-motion preference.
