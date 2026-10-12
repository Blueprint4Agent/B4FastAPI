# Publication and release evidence

[한국어](ko/publication.md)

Blueprint4FastAPI provides application foundations and a repeatable development workflow:
FastAPI/React contract checks, authentication, role boundaries, realtime refresh,
background mail, shared UI and Docker packaging. It is a starting point for a service;
its presence alone does not certify a particular deployment.

## Local preview

Follow the root README quick start, keep APP_MODE=development and open
`http://localhost:5173/show-case`. The README screenshots were captured from the
packaged frontend served by an isolated local Docker app, with disposable SQLite and
external email/OAuth/Stripe disabled. They show the existing component library, not
an online hosted demo. Production redirects the development showcase to the home page.

## Public description

Use: “A FastAPI + React blueprint with typed API contracts, authentication and a
repeatable workflow for agents and developers.” Explain optional integrations as
configuration-dependent. Keep screenshots current with the pinned B4React version.

Before claiming a release is ready, record the parent/child revisions and actual Make
results, build/startup/readiness evidence and the environment tested. Validate domain
TLS, login/refresh, enabled provider callbacks and database backup/restore in the target
environment. Desktop distribution additionally requires signing and installation checks.
Manual GitHub workflows and local verification are distinct; do not imply automatic CI.

## Reuse and identity

Retain the MIT license and third-party notices. Configure your own identity through
[project setup](../PROJECT_SETUP.md), and use your own domain and provider accounts.
No hosted demo, performance SLA, external-provider certification or security audit is
implied by the template. Report issues with reproduction steps and redacted configuration;
do not publish tokens, passwords or customer data.

The pinned frontend includes its MIT notice and reviewed dependency updates. Configure
[static sharing metadata](../DEPLOY.md#public-sharing-metadata) with your real public
origin before distributing a deployment link. Audit results are time-bound; rerun
`npm audit` in the child when preparing a later release.

Search publication and community drafts: [search discovery](search-discovery.md). Keep local implementation, merged source, deployed pages, submitted URLs and indexed results as separate evidence.
