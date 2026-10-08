# Commit Title

fix(logging): separate method and severity color palettes

# Changed File Scope

Backend console formatters, palette regression tests, English/Korean logging guides
and this worklog.

# Reason

Inherited Uvicorn severity colors overlap HTTP methods (INFO/GET, WARNING/PUT,
ERROR/DELETE). Give each category its own palette and tint severity message bodies.

# Design

Keep the seven method colors; use distinct 256-color severity labels and softer
message colors. Separate time/path and HTTP status colors too. Severity labels are
bold; CRITICAL uses a dark contrasting background. Style only record copies so
file/OTLP originals, plain output, correlation data and tracebacks remain intact.

# Verification Plan

Root make verify-plan and make verify. Update existing palette expectations and inspect actual RGB uniqueness across
roles, message styling, plain/colored text equivalence and original-record preservation
with an isolated formatter check. Inspect a terminal preview before commit.

# Impact

Console presentation only. Extended colors require a 256-color-capable terminal;
NO_COLOR and redirected output remain uncolored. No API, schema or filtering changes.

# Loop Alignment

Request, domain-event and background-task loops are not applicable to color-only
console rendering. Frontend loops are not applicable; no frontend files change.

# Verification

- Root make verify-plan selected backend runtime and text checks; make verify
  passed Ruff, architecture, environment/OpenAPI contracts and 389 backend tests.
  No selected checks were omitted. Frontend runtime/browser checks were not selected
  because no frontend files change.
- An isolated formatter check confirmed 26 unique actual foreground RGB values,
  styled severity labels and message bodies, equal colored/plain visible text and
  unchanged original message/arguments.
- Interactive terminal preview confirmed the method/status palette plus TRACE,
  DEBUG, INFO, WARNING, ERROR and CRITICAL styles and message tints.
- Existing uncolored/NO_COLOR, file-handler, traceback and request-context coverage
  passed. Runtime request/event/task loops and frontend loops are not applicable to
  this console-only color update.
