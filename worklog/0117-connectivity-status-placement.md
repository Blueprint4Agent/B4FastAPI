# Commit Title

fix(frontend): place connectivity status in navbars

# Changed File Scope

- Frontend layout components for app, public, and desktop titlebar navigation.
- Desktop connectivity status component, styles, locales, and retry UI behavior.
- Server-unavailable and landing page navbar structure.
- Component and integration tests for connectivity placement, retry stability, and offline logout blocking.
- Frontend README/FRONTEND/TEST documentation and Korean localized documentation.

# Reason

The desktop server-disconnected notice was shown as a page-level UI and could visually shift navbar
content when retry state changed. Manual retry also briefly flashed loading UI, and signing out while
the desktop server was unavailable cleared the local session and routed the user to `/login`.

# Impact

- Desktop server status now appears beside the app profile control or standalone/public navbar theme
  control.
- Landing and server-unavailable pages share the same public navbar structure.
- Reserved navbar status width keeps centered titles stable when status state changes.
- Manual retry keeps the disconnected label stable and delays heavier loading indicators.
- Profile-menu sign-out is disabled while packaged desktop connectivity is not online.

# Verification

- `make frontend-format-check`
- `make frontend-test`
