# Commit Title

`fix(frontend): lock routes when config unavailable`

# Changed File Scope

- Frontend application configuration state and protected route guard
- Server-unavailable retry page and localized messages
- Navbar identity fallback behavior
- Application and configuration hook regression tests
- English and Korean frontend engineering, usage, and test documentation

# Reason

When `/config` failed during offline startup, the frontend interpreted missing configuration as
`login_enabled=false`. That fail-open default allowed protected pages to render without a verified
session and displayed a hardcoded `User` identity fallback.

# Impact

- Protected routes remain locked until `/config` succeeds.
- Login-disabled routing is allowed only after an explicit server response.
- Offline startup shows a server-unavailable page with a retry action.
- The navbar no longer renders a fabricated user identity when no user exists.
- Previously loaded configuration remains usable during a later transient outage.

# Verification

- `make frontend-format-check`
- `make frontend-test`
- `make frontend-build`
- `make frontend-desktop-build`
