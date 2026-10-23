# Commit Title

perf(verification): select page suites and separate visual matrices

# Changed File Scope

scripts/verification_scope.py and regression fixtures (mirrored independently), browser/component tests, capture helper, verification cache artifact guard, bilingual verification docs; parent gitlink integration.

# Reason

B4React #94: ordinary page edits run unrelated suites, and viewport/theme matrices repeat complete mutation flows.

# Design

Connect reviewed page/feature/hook owners to existing test files, deduplicate unions and broaden on shared/unknown/missing coverage. Keep business journeys canonical and use prepared states for visual matrices. Successful screenshots are explicit opt-in artifacts, not image assertions. Preserve behavior assertions and security/provider branches.

# Verification Plan

One original scoped UI baseline on an isolated data-attribute probe; classifier fixtures and related browser/unit suites while editing; root Make plan/verify once final; probe first/reuse/parent integration measurements; child-first ready PR, governance and merge commits.

# Impact

Verification/test ownership only; no application runtime/contract changes. Backend domain selection is a separate #152 task.

# Loop Alignment

App request/event/task and frontend API/realtime/desktop/UI composition implementations are unchanged. Tests retain recovery, persistence and geometry assertions; no runtime loop is skipped.

# Verification

Child B4React #96 merged at b77debffcdb8b6f4b66ef6e7f8fc5bcc6cd6e79e; tree equals tested implementation 1729a4d. Child full Make verification passed (63 Python fixtures, 208 Vitest, 253 UI, 15 production, 11 discovery, 3 editor). Inbox JSX probe: original 82.61 s, scoped 16.21 s, unchanged repeat 0.45 s. Probe restored exactly. Parent classifier copies/cache guard and bilingual notes are synchronized; backend runtime/tests are unchanged and backend suite is omitted for that reason. Root integration selected frontend/harness/branding contracts (backend omitted as unchanged), passed in 26.4 s (run-uxjc6lng), reused all 9 child commands, and retained local parent fixture/custom-brand/contract/packaging checks. Final-code Inbox probe: first 14.87 s (3 fresh commands, 7 browser tests, no Vitest because no dedicated owner file), repeat 0.42 s (3 reused), parent integration 0.88 s (5 commands, child proof reused; branding/contracts/packaging retained). Probe restored exactly. Final branch verification after restoring the probe passed in 10.3 s, reusing unchanged checks and rebuilding/retesting production output that the temporary probe had changed. These are single local samples, not universal UI latency guarantees.
