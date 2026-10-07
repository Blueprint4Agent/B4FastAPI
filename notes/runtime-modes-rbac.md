# Runtime modes and roles

[한국어](ko/runtime-modes-rbac.md)

`APP_MODE=development|production` controls product behavior, independently of the
`APP_ENV` telemetry label and Vite's build mode. The default remains development
for local compatibility. The Docker example explicitly selects production.
Production requires `LOGIN_ENABLED=true`; unknown modes or login-free production
fail configuration/startup validation. Set the mode explicitly for deployments
and deploy the coordinated backend `/config` contract and B4React together.

Both modes open the template home (`/home`) by default, including for guests. Account
actions still require authentication. Development exposes GitHub, User guide and a
separate component showcase menu. Production
omits these links, redirects direct showcase/preview URLs to the template home (`/home`), and never renders a showcase behind authentication dialogs. Normal user
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

## Administrator server status

`GET /api/v1/admin/status` requires the current database-backed admin role (managers
cannot read it). The read-only screen at `/admin/server` follows the settings/home
page shell. It probes the actual database dialect and Redis, with concurrent
2-second dependency timeouts shared with `/health/ready`. In-memory Redis is
identified explicitly. A successful API request establishes server reachability;
worker health and historical observability are outside this snapshot.

The response allowlists effective email, login, OAuth, payment/subscription,
development UI and runtime modes. Administrator access is a role policy, not an
`ADMIN_ENABLED` environment flag. It never returns connection URLs, credentials,
keys, or arbitrary environment values. Feature flags describe configuration,
not delivery or third-party connectivity tests. Settings are captured from the
running process; changing an environment file requires the normal server restart.

The page refreshes every 30 seconds while visible and on focus/reconnection.
Requests are canceled on leaving or changing the account. Failed refreshes and
snapshots older than 60 seconds show stale results; requests time out after 8
seconds. A database outage can also prevent authentication, so the page retains
only clearly marked stale information; it never bypasses the admin dependency.

Completed startup verification is exposed separately with its original timestamp:
Stripe API authentication/resources and optional SMTP handshake/authentication may
show healthy at startup; OAuth validates configuration only and never claims a
completed user login. Disabled or skipped checks never become healthy merely from
an enabled flag. Refreshing this screen separately checks current email/Stripe connectivity without sending email. These startup results are historical evidence, not live health.

While administrators view the page, SMTP connection/authentication and a Stripe
Checkout list read run at most once per 60 seconds per process. Concurrent requests
share a probe. The API waits at most five seconds for provider results and reports
a timeout while an existing operation finishes; SMTP sockets use two-second waits
and Stripe retains its provider timeout. No email or billing resource is created.
No new checks are scheduled after leaving the page. Multi-process deployments have
one cache per process. OAuth has no health badge because configuration or endpoint
reachability cannot establish a successful user-authorized sign-in.

Database and external Redis cards expose only their configured hostname and effective port to
administrators. Credentials, database name, query options and local filesystem
paths remain excluded. SQLite is labeled as a local file; socket connections have
no fabricated network hostname.

The environment screen pairs localized effective meaning with allowlisted actual
boolean/runtime-mode values. `environment_values` is an explicit typed projection,
not a settings/environment dump. CodeBadge is shared with the frontend showcase.

## Disabled feature boundaries

Public `/config` exposes effective `billing_enabled` and `subscriptions_enabled` flags.
`STRIPE_ENABLED=false` removes billing shortcuts, settings navigation/content, plan routes
and profile tier/upgrade UI. Billing hooks remain idle until configuration explicitly
allows the feature, including focus/online/desktop recovery. Direct disabled URLs fall
back to Home (plans) or General settings (billing). With Stripe enabled but subscriptions
disabled, payment methods, billing profile and invoice history remain available; plan
selection, subscription reads and checkout-return requests do not run.

Enabled Stripe performs a read-only API authentication check during FastAPI lifespan.
Authentication rejection, permission errors, invalid configuration and connection failures
abort startup before migrations/serving. Disabled Stripe performs no provider request.

Login-disabled mode rejects signup, refresh and email/OAuth entry mutations before I/O.
Email-disabled mode rejects direct email verification without consuming the token; password
reset and account deletion retain their existing guards. Verification resend remains an
account-neutral no-op when email is disabled. Email-only routes and OAuth entry UI are
hidden according to public config. OAuth callbacks check the current feature/provider
configuration before consuming state or exchanging a code. Password login/signup continue
working with email and OAuth disabled; new email accounts are already verified in that mode.
Feature settings are process configuration, so changing environment values requires restart.
