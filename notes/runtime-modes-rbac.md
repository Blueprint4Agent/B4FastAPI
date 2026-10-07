# Runtime modes and roles

[한국어](ko/runtime-modes-rbac.md)

`APP_MODE=development|production` controls product behavior, independently of the
`APP_ENV` telemetry label and Vite's build mode. The default remains development
for local compatibility. The Docker example explicitly selects production.
Production requires `LOGIN_ENABLED=true`; unknown modes or login-free production
fail configuration/startup validation. Set the mode explicitly for deployments
and deploy the coordinated backend `/config` contract and B4React together.

Development exposes GitHub, User guide and the component showcase. Production
omits these links, redirects direct showcase/preview URLs to account settings or
login, and never renders a showcase behind authentication dialogs. Normal user
API-key management remains a product feature. Runtime gating does not remove
showcase JavaScript from the shared build. The separate Style Studio remains an
explicitly enabled loopback-only development tool, not a production API.

Login-free development uses only a dedicated active bootstrap identity without a
password. A matching normal-account email or a bootstrap identity whose role was
changed fails startup; no existing account is promoted automatically. Production
never provisions bootstrap identities and rejects their bearer sessions and API
keys, including tokens issued before switching modes. It does not delete their
data or silently convert them to ordinary accounts. Review linked data before
retiring old development identities; use a separate real account in production.

| Permission | User | Manager | Admin |
| --- | --- | --- | --- |
| Own account, API keys and billing | Yes | Yes | Yes |
| Read user directory and role statistics | No | Yes | Yes |
| Implicit access to admin-only guards | No | No | Yes |
| Change another user's role/profile/billing over HTTP | No | No | No |

Roles are explicit allowlists, not an automatic inheritance hierarchy. Managers
can read names, email addresses and the existing directory metadata, but cannot
edit other accounts. Future administrator endpoints must opt in explicitly.

Provision the first administrator from a normally registered/OAuth account:

```sh
make user-role EMAIL=operator@example.com ROLE=admin
make user-role EMAIL=manager@example.com ROLE=manager
make user-role EMAIL=manager@example.com ROLE=user
```

The CLI requires login enabled and access to the intended backend environment.
The standalone command registers its related ORM models independently of server startup.
No role-change HTTP API is introduced. Current DB roles authorize subsequent
requests without reissuing tokens; reload account data to refresh navigation.
The last active administrator cannot be deleted or demoted to either user or
manager. Role changes and their audit rows commit atomically. No-op assignments
create no audit entry. `role_change_audit` stores target numeric ID, old/new roles,
UTC time and the CLI OS username (`cli:...`), not a verified application actor.
This is a trusted-operator record, not tamper-proof auditing. It contains no email
or credentials and is retained after account deletion; operators control access
and retention through DB operations, not an exposed management endpoint.

Apply migration `0010_role_change_audit` before deploying. The existing role
column is VARCHAR(20), so existing values need no conversion on upgrade. Before
rolling back to a two-role release, export required audit records and downgrade:
the migration demotes managers to users and drops the audit table. It preserves
existing administrators and users. Back up and review the target database first.

Environment examples use section dividers and a `Values` comment directly above each managed variable. `make env-sync docker-env-sync` synchronizes layout/comments with backups while preserving existing values and extra keys. Local `.env` files and backups are not committed.
