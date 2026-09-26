# Commit Title

fix(api-key): preserve committed results and reconcile realtime state

# Changed File Scope

Backend realtime service and API Key publication policy; backend docs.
Then B4React domain state hook, SSE reconnection handling, settings composition,
and parent submodule pin after the frontend PR merges.

# Reason

Redis notification failure must not convert a committed API Key operation into an
HTTP failure. HTTP and SSE arrivals must not duplicate records, and reconnects
must recover changes missed by non-durable Redis pub/sub.

# Design

First add an explicit bounded best-effort publication path for API Key UI events,
logging delivery failures without raw keys/payloads and preserving cancellation.
Then centralize API Key list/mutation state in a page-owned domain hook, share
ID-based updates, reject stale list responses and reload on SSE connection/tab
activation/desktop recovery. Retain modal/input state in the page.

# Verification Plan

Run root Make static/contract/architecture checks and frontend build. Existing
PR CI tests remain enabled; local/new tests were not requested for this task.

# Impact

API contracts and DB storage stay unchanged. Notifications remain best-effort,
not durable delivery; clients reconcile with authoritative list responses.

# Loop Alignment

Preserve Router-Service-Repository request ownership. Separate committed writes
from UI event transport failures. Domain state hook owns HTTP/SSE reconciliation
and reconnect recovery; feature components remain prop-driven. Worker behavior
and visual composition are unchanged.

# Verification

- Root make check passed: backend lint/format, architecture, environment contract,
  frontend format/types, OpenAPI contract and generated client consistency.
- Frontend make check and make build passed.
- No local/new tests requested; existing required PR CI remains enabled.
- No live Redis fault injection or browser timing reproduction performed.
- Planned staged governance validation runs before each repository commit.

- B4React PR #3 merged as 1d4545bc536fc8f84386b8c1b9745e8f4cd63bb0.
- Child required CI passed after aligning four existing fixture assumptions with
  lazy loading, canonical order and persisted mock status changes.
- Child staged governance passed for both authored commits.
