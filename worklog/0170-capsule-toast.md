# Commit Title

feat(ui): add capsule toast feedback for user actions

# Changed File Scope

Pinned src/frontend gitlink and this integration worklog. Runtime changes, bilingual docs and component/browser regressions belong to B4React.

# Reason

Provide a compact fullscreen-notification-style capsule with a short message that appears briefly and disappears automatically, with an interactive showcase example.

# Design

Mount-driven ToastCard portals to body at viewport top center, uses a single plain-text message and a polite status region, defaults to three seconds then a short exit animation, and cleans timers on unmount. A keyed isolated ToastPreview replaces/replays the current toast instead of stacking. Reuse Button, inverse theme tokens and shared CSS; preserve focus and pointer access to the underlying page. Respect reduced motion. The child provides stable dispatch for one route-persistent action notification; no fullscreen API is introduced.

# Verification Plan

Root frontend-format-check and frontend-test. Child make check/test/build/test-ui. Fake-timer component cases cover expiry, replay/unmount and callback changes; browser cases cover actual delayed dismissal, focus, mobile/desktop placement, theme contrast and reduced motion. Inspect screenshots. Validate staged governance before commit.

# Impact

No API contract, dependency or persisted state change. Signup/reset-email confirmations now wait for successful responses. Toast is transient feedback, not a place for required actions or critical persistent errors.

# Loop Alignment

UI composition uses shared Button/CSS and rendered catalogue coverage. API state remains domain-owned with explicit action result feedback; API-key callbacks respect current account epochs. Automatic refresh/SSE/bootstrap/desktop recovery keep existing persistent feedback without repeated toasts. Backend request/event/background loops are not changed.

# Verification

Parent make frontend-format-check frontend-test passed (93 tests). Child make check/test/build passed; test-ui passed 65 browser cases and test-routes passed 6 production cases. UI geometry/contrast/focus/expiry and provider render isolation verified. No required checks skipped. B4React PR #26 merged as 852c0e79b1b8d435f247458b5df2a072d18e4250 after Git governance and Frontend checks passed; MERGE registration verified. Validate staged Git governance and required parent CI.

# Expanded Implementation Plan

Review user-triggered authentication, recovery, profile, API-key and clipboard outcomes. Add a route-persistent provider with a stable dispatch-only context and one replaceable notice. Keep detailed inline errors and field validation; background refresh/SSE/bootstrap errors do not generate notifications. Await signup/reset-email responses before confirmation navigation, fixing silent failures. API-key mutation callbacks remain epoch-guarded and UI-independent. Add outcome, route persistence and render-isolation regression coverage.
