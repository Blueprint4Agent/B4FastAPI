# Commit Title

feat(discovery): integrate public search pages and publication workflow

# Changed File Scope

Public discovery build assets, English/Korean content and documentation, crawler policy, build configuration and regression coverage.

# Reason

Expose an accurate B4A introduction without JavaScript or authentication while retaining the existing application home and account flows.

# Design

Opt-in public discovery build generates /about/ and /about/ko/ with canonical/hreflang, shared home styling and localized feature copy. Only these public pages enter the sitemap. Search crawlers are allowed; OpenAI/Anthropic training bots are blocked. App HTML is noindex when discovery is enabled. Require a configured public origin and default template identity; custom projects cannot accidentally advertise B4A. No API or database changes. Parent adds build-argument plumbing, publication runbook and changed-URL IndexNow tooling.

# Verification Plan

Run root Make verify-plan and verify at the full branch scope. Add static HTML, crawler/sitemap/escaping/custom-brand guard and JavaScript-disabled browser checks; compare home typography/surfaces at desktop/mobile and light/dark. Verify packaged FastAPI static responses before claiming rollout readiness.

# Impact

Opt-in build-time behavior, no migration. Existing app routes remain unchanged. Live search registration, DNS ownership and remote deployment require actual account/server access; never claim them from local builds. Community copy is prepared for review, not posted.

# Loop Alignment

No new API requests, domain events or background tasks. Existing auth/config/realtime/connectivity owners remain unchanged. Static introduction reuses home CSS, semantic links and localized copy. IndexNow is deployment tooling rather than request-handler work.

# Verification

- Root `make verify-plan` selected backend checks and full frontend scope because runtime/build configuration changed. `make verify` passed: 478 backend tests, hooks, architecture/environment/OpenAPI checks, packaging/contracts and isolated custom-brand build/route checks.
- Reused unchanged child verification receipts: 168 unit/integration tests, 214 browser UI tests, 10 production route tests, 11 public discovery tests, static/type/format/policy and style-studio checks. No required checks were omitted; duplicate child execution was avoided using content-bound receipts.
- IndexNow's five script tests passed, including dry-run, rejected paths, failed submission state preservation and deleted-page SPA rejection. Deployment smoke ordering and static 404 behavior are covered by backend regressions.
- Generated discovery build served through actual FastAPI TestClient: `/about/`, `/about/ko/`, `/robots.txt`, `/sitemap.xml` returned 200 with HTML/plain-text/XML types; missing public document returned 404. Live local Vite `/about/ko/` also returned static HTML with development noindex.
- B4React PR #82 merged first; parent pins `c3e8e69`. No remote deployment, site verification, sitemap submission or community posting performed. Publication/deployment are separate operational steps.
- Loop alignment: no request/domain/background/realtime state loop was introduced; static documents and post-deploy notification tooling require none.
