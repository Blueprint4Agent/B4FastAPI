# Commit Title

feat(auth): align authentication UI and email templates

# Changed File Scope

src/frontend submodule pin, backend mail templates, tests, bilingual guides and this worklog.

# Reason

Expose the showcase to guests and present existing authentication through compact
login/signup/recovery dialogs from a guest profile menu.

# Design

Adopt the merged B4React change after required child checks. Expose guest General/Appearance while protecting account-only
settings and fail-closed configuration handling. No parent API/contract changes. Email HTML uses a shared 480px inline table layout,
neutral palette, 22px headings, 14px body, compact rounded CTA and quiet notice.
Keep subjects, plaintext, URLs and queued sending intact; escape dynamic HTML.

# Verification Plan

Run root frontend-format-check/frontend-test against the merged child pin and
verify child/parent required CI before merge. Run root make check/test for the
expanded cross-stack scope and render EN/KO verification/reset emails at mobile
and desktop widths.

# Impact

Public entry opens the showcase; login supports configured Google/GitHub and the
existing email/password flow. Guest copy says start your own project. Shared modal
backdrops use transparent blur, and profile triggers receive additional padding.
Recovery/verification states share the auth frame, and reusable pill buttons plus
compact feedback cards are demonstrated in the showcase. Anonymous entry uses
the localized Log in / Sign up label.

Recent accounts retain opted-in metadata only and require reauthentication; avatars
are circular and account switching opens in an adjacent popup. Guest settings expose
General/Appearance without account API requests.

# Loop Alignment

UI composition uses shared Modal and existing auth hooks. API state remains owned
by auth pages/hooks. Realtime and desktop recovery remain unchanged. Backend request/event loops are unchanged; mail delivery stays in the existing
background task loop, with only HTML rendering changed.

# Verification

Root make check/test passed: 74 backend and 62 frontend tests. Child check/test/build
and 39 browser cases passed. Reviewed mobile/desktop auth and account picker screenshots,
and EN/KO verification/reset email renders at 390px/700px. Email tests validate escaping,
links and plaintext preservation; no live emails sent. B4React PRs #11/#12 merged; child pin 17dc0319e357e381afd12cd93940d7a672e2285d.
Child required CI passed; parent CI required before merge.
