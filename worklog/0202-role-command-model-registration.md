# Commit Title

fix(auth): register related models in role command

# Changed File Scope

Role-management CLI, subprocess regression tests and English/Korean runtime role documentation.

# Reason

A fresh CLI process imports User without APIKey, so mapper initialization fails before the role update even against an up-to-date database. In-process API tests mask the missing import.

# Design

Explicitly register the User relationship's APIKey model at the standalone entry point. Keep schema migration and account provisioning separate. Exercise the real Python module in fresh subprocesses against an isolated test database, including role assignment and last-admin denial.

# Verification Plan

Reproduce with pdb, inspect schema and target account without exposing secrets, add fresh-process regression coverage, run root make verify-plan and make verify, then retry the user's exact command and verify the role/audit row.

# Impact

Restores existing CLI role assignment without changing API contracts, schema, or frontend. No automatic migrations or account creation.

# Loop Alignment

CLI uses existing transactional repository role/audit writes. HTTP lifecycle, domain-event/background-task, realtime and frontend loops are not applicable to this standalone model-registration fix.

# Verification

pdb observed InvalidRequestError: User mapper cannot resolve APIKey; the target database already had migration 0010 and an active target account. Both fresh-process regression cases failed before the fix and all 8 role-command tests passed afterward. Root make verify-plan / make verify passed (backend=True, frontend=docs), including 234 backend tests, architecture/environment checks and contract validation. Frontend runtime/UI/build checks were omitted by the classifier because no frontend behavior or contract changed. Retried the requested command successfully and verified the persisted admin role and user-to-admin audit record. Debugger breakpoints were cleared and the session was stopped.
