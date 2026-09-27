# Commit Title

feat(auth): expose admin user directory

# Changed File Scope

Auth router/service/repository, contract, tests and EN/KO docs

# Reason

Administrators need a dedicated user monitoring panel accessible from their profile menu.

# Design

Paginated read-only admin directory: identity, role, status, providers, joined date and latest successful login. Reuse auth errors/dependencies; no schema migration or role editing API. Commit provider snapshot for immutable child adoption.

# Verification Plan

Backend Make checks/tests and contract export; child check/test/build/test-ui; final parent check/test/build and governance.

# Impact

Read-only administrator access; ordinary users cannot read the directory. Existing login/role management stays intact.

# Loop Alignment

Backend route -> admin dependency -> auth service -> repository. Read-only feature needs no new events or background tasks. Frontend uses typed auth API/hook, focus refresh and desktop recovery; shared sidebar and UI composition. No online-presence claim or durable login audit in initial scope.

# Verification

Passed `make backend-format backend-check backend-test` (82 tests) and contract export. Backend request lifecycle and admin dependency preserved; reads need no events or background tasks. Cross-stack contract equality/check/test/build are deferred to the integration commit after the child adopts this immutable provider snapshot; current child intentionally uses the prior baseline. No operational data changed.
