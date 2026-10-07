# Commit Title

feat(frontend): integrate default home template

# Changed File Scope

Shared default home routing in both runtime modes, shared-sidebar home destination, localized home content, browser coverage and integration documentation.

# Reason

Production has no default content page after hiding the developer showcase and currently redirects signed-in users into account settings.

# Design

Provide a minimal public home using the existing application shell and settings-family header/surfaces. Show real account greeting and shortcuts to account, billing, preferences and role-allowed directory. Guests see generic navigation and sign in for account access. Both modes default to home; development alone retains a separate showcase link. Login success, logout, auth close and page recovery return home. Preserve admin billing and subscription behavior unchanged. No fabricated metrics or new APIs. Follow-up scope: extract MainPageTemplate with typed menu items, list/grid arrangement, header actions and children slots; demonstrate extension in the developer showcase and localized docs.

# Verification Plan

Root Make verification, production home and auth/redirect browser checks, responsive light/dark English/Korean peer comparisons, production chunk loading and recovery.

# Impact

Both runtime modes use /home for root/dashboard and auth completion/close. Production redirects showcase URLs home; development exposes a separate showcase menu. Guest home contains no private account data. Existing setting destinations remain available.

# Loop Alignment

Reuse shared auth/config ownership and existing connectivity recovery. No API fetches, realtime subscriptions, mutations, domain events or background tasks are added.

# Verification

B4React PR #54 merged at 4f033a3361ce53cf31173353ddf4ea7234bafffa before the parent gitlink update. Child full verification and pre-push checks passed: 125 frontend tests, 131 browser UI tests, 9 production route tests and 3 Style Studio tests; actual child PR governance passed. Root plan selects backend=False/frontend=full; backend runtime checks are omitted because backend behavior/contracts are unchanged. Parent make verify-plan / make verify passed: hooks, child checks/tests/UI/routes/Style Studio, frontend contract comparison/packaging and project build fixtures. No selected checks were omitted. Admin billing and subscription behavior is preserved.
