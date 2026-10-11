# Commit Title

fix(docker): persist SQLite data across container recreation

# Changed File Scope

Compose volumes, deployment preflight, deployment fixtures, env example comments and EN/KO deployment guides.

# Reason

The documented SQLite database path resides in the disposable application container layer.

# Design

Mount a dedicated database volume into app and worker. Require SQLite DB_NAME to be an absolute path inside that volume in the deployment preflight. No automatic move or deletion of existing data; document operator migration before recreation.

# Verification Plan

Root make verify-plan/verify; isolated Docker image and named-volume recreation probe; preflight acceptance/rejection regressions. Existing frontend receipts may be reused.

# Impact

PostgreSQL selection remains unchanged. Old SQLite deployment paths fail early and require a backup/move before recreation. In-memory Redis remains single-process, non-durable development behavior.

# Loop Alignment

Deployment startup selects persistent resources before request processing or worker publication. Request, domain-event and frontend loops are unchanged; worker shares the same SQLite file when selected.

# Verification

- Root verify-plan/verify against origin/main passed: full scope; 450 backend tests passed. TERM=xterm-256color retained for the existing terminal fixture.
- Unchanged frontend checks reused matching content-bound receipts; integration contracts/package and isolated branding checks passed.
- Docker image built successfully; Compose config validated. A fresh SQLite volume survived container removal/recreation with the same marker and healthy migrations/readiness in both containers.
- Only temporary probe containers/volumes were removed. Production migration and external integrations were not exercised because this change does not authorize modifying live data.
