# Commit Title

feat(logging): distinguish request fields with terminal colors

# Changed File Scope

Backend console formatters, request-log tests, English/Korean logging guides and
this worklog. Follow-up in the existing lifecycle/console PR.

# Reason

Differentiate HTTP verbs, timestamps and API paths at a glance while retaining the
same readable plain-text layout in container/file output.

# Design

Use gray timestamps, bright-blue paths and method-specific colors: GET green,
POST cyan, PUT yellow, PATCH magenta, DELETE red, HEAD blue, OPTIONS gray. Pad
visible method/path text before applying ANSI styles. Preserve status colors,
original LogRecords and handler-aware NO_COLOR/nonterminal behavior.

# Verification Plan

Run root make verify-plan and make verify. Check method colors and column alignment
with ANSI parsing, preserve uncolored-output tests and inspect a terminal preview.

# Impact

Console appearance only; no API, dependency, CORS, filtering or execution changes.

# Loop Alignment

Request lifecycle, event/task and frontend loops are unchanged. This updates only
console formatter fields, not request handling or state propagation.

# Verification

- `make verify-plan` selected backend runtime/documentation checks; `make verify`
  passed Ruff, architecture, environment/OpenAPI contracts and 389 backend tests.
  No selected check was omitted. Unchanged frontend checks use the earlier full
  verification evidence; branch-wide pre-push checks validate receipt applicability.
- Terminal preview confirmed all seven HTTP verb colors, gray timestamps,
  bright-blue paths and the aligned INFO/WARNING/DEBUG/ERROR/CRITICAL palette.
- ANSI-parsed colored/plain text has identical visible column positions. Tests
  preserve original LogRecord arguments and reject color on redirected/NO_COLOR
  streams. Existing request/error/file-handler regressions also passed.
- The backend suite continues to report dependency deprecations and asyncpg
  cancellation warnings; these are not suppressed by the console styling changes.
