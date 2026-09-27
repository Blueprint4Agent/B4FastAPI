# Commit Title

feat(dev): launch local showcase style editing

# Changed File Scope

Root Make launch target, EN/KO development docs, pinned B4React.

# Reason

Connect an explicitly enabled local development server to its frontend source, preview showcase style tokens without writes, then apply reviewed changes.

# Design

An opt-in Vite development middleware owns access to its own resolved frontend root and only src/styles/app.css. It validates a bounded token schema, same-origin loopback requests and a per-process capability header; optimistic file hashes reject stale writes. Apply backs up and atomically replaces the file. The showcase exposes a lazy development-only animated right panel with custom color/number/dropdown controls; theme mode reuses the global preference while drafts stay scoped to the catalogue; browser drafts override CSS variables only within the showcase and are removed on exit. Light/dark colors and shared geometry are explicit. Production has neither editor code nor middleware. No arbitrary filesystem paths, commands or parent reads are exposed.

# Verification Plan

Make check/test/build; middleware fixtures for opt-in, path boundaries, origin/token guards, validation, backup and stale revision; UI tests for draft/reset/apply/conflict and mobile layout. Production bundle absence check. Root make check test build and required PR CI.

# Impact

Developer opt-in only; persisted changes are normal app.css edits visible in Git and Vite HMR. No auth/API/database schema changes. Parent launch target selects the frontend folder explicitly.

# Loop Alignment

Frontend page -> domain hook -> development API wrapper -> local middleware. No backend request/event/task loops because this is a local Vite tool, no FastAPI endpoints. Preview is local state and applied CSS refresh uses existing HMR; no new SSE or desktop recovery. Shared inputs/buttons/styles reused.

# Verification

Passed root make check test build: 82 backend and 81 frontend tests plus format/types/contracts/architecture and packaging; earlier initializer verification passed 9 cases. Child checks passed 4 filesystem/middleware fixtures, 3 style editor browser flows at 390/1440px, 54 existing UI tests, and 6 production tests including editor/protocol absence. Production entry is 397.41 kB / gzip 123.44 kB after adding shared ColorPicker and NumberField catalogue examples. The explicit loopback development server remains running; Korean visual inspection confirmed the right panel, global theme, field alignment and minimal anchored palette. Native packaging is not applicable to this browser development tool; backend event/task/recovery loops are not used because no FastAPI/runtime API changes were introduced. Integrate merged B4React PRs #22 and #23; required PR checks must pass before merge.
