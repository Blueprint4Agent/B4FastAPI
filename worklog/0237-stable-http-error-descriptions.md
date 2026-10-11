# Commit Title

fix(contracts): stabilize HTTP error descriptions across Python versions

# Changed File Scope

Error response contract helper, OpenAPI regression tests, EN/KO contract notes and worklog.

# Reason

GHCR retry 38130742332 passed 459 tests but failed contract-check. Python 3.12 HTTPStatus uses older phrases for 413/422 than local Python 3.13. Docker reproduced six description-only differences against the pinned baseline.

# Design

Pin the existing baseline phrases Content Too Large and Unprocessable Content for generated domain errors. Keep other HTTPStatus descriptions and all response codes, models and payloads unchanged. Add regression coverage for profile-photo GET/PUT/DELETE descriptions. No baseline regeneration or frontend contract changes.

# Verification Plan

Export the schema with the Python 3.12 Docker image and mounted changed helper, compare the full baseline, then run root make verify-plan and make verify. Publish the final main through the full manual Build workflow.

# Impact

Stable descriptive API metadata across supported Python versions; no transport, auth or billing behavior changes.

# Loop Alignment

Shared error metadata remains on the existing router/service/error path. No event, task or frontend state loop changes.

# Verification

Python 3.12 Docker export with the changed helper matches contracts/openapi.json byte-for-byte. Root make verify-plan and make verify passed (backend=True, frontend=full): 462 backend tests, contract/architecture/environment checks, frontend packaging and 10 fresh project-build route cases. Unchanged child check/test/browser/route/style receipts were reused; no manual scope downgrade. Existing published contract is unchanged.
