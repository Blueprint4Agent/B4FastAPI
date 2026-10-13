# Commit Title

feat(frontend): integrate the product landing home

# Changed File Scope

Pinned B4React gitlink, notes/frontend-submodule.md, notes/ko/frontend-submodule.md and this worklog. Home implementation and browser coverage are owned by the child.

# Reason

Replace the settings-like first screen with a restrained product landing page, using the referenced dailoom.co hierarchy as inspiration rather than copying its appearance or content.

# Design

Keep the selected app shell and all role/auth gates. Introduce a documented home-landing family with a wider two-column introduction and actual product preview, compact text preview navigation, grouped unboxed capability lists, an honest source/documentation starting point and compact account links. Reuse Button, Modal, existing product screenshots and theme tokens. Preserve public discovery output and standalone page families. No backend contract or new data request.

# Verification Plan

Run make verify-plan / make verify and browser comparisons at desktop/mobile, EN/KO, light/dark and all three service layouts. Preserve preview selection, modal keyboard behavior, roles, guest login, production route loading and static introduction checks.

# Impact

Home presentation/copy changes; account destinations, previews, auth overlays, layout defaults and deployment options remain available. No invented usage metrics, testimonials or provider readiness claims.

# Loop Alignment

UI composition follows existing Button/Modal and theme tokens. API/auth/realtime state remains in existing owners; no new API calls/events/tasks. Desktop recovery remains in the app shell; backend lifecycle/event/background loops are not applicable.

# Verification

B4React implementation PR #86 and documentation-format follow-up #87 are merged; pinned revision 4796704399d252450d6aeed248f885506080bd6f. Child full verification passed 195 unit/component/integration tests, 227 UI browser cases, 10 production-route cases, 11 static-discovery cases and 3 style-studio cases, plus policy/type/format checks. Browser review covered mobile/desktop, EN/KO, light/dark and all service shells. Root make verify-plan selects full frontend integration with backend=False. Root make verify passed hook/project-brand checks, the full child frontend suite under the integration context, exact OpenAPI contract equality, verified dist packaging and an isolated custom-brand production build. Logs: /tmp/b4-home-parent-verify.log and .git/verification-logs. The format-only child follow-up corrected the final evidence paragraph before packaging; no runtime code changed. Backend/native checks are omitted locally because no backend/native behavior changed; remote image workflow remains full.
