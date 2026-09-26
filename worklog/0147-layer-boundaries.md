# Commit Title

ci(architecture): enforce application layer boundaries

# Changed File Scope

Architecture checker, Make/CI integration, domain guide and bilingual README.
Parent also pins the merged frontend checker revision.

# Reason

Detect concrete dependency violations of the documented backend/frontend layering.

# Design

Backend: parse Python AST imports, prohibit Router DB dependencies and non-schema
model imports, and prohibit lower layers importing Routers/app composition root.
Frontend: use the existing TypeScript compiler to resolve imports including aliases
and barrel exports; allow explicit type-only imports, prohibit UI runtime API imports
and component runtime domain-hook imports, and detect direct browser HTTP calls.
No new runtime dependencies or business-flow changes.

# Verification Plan

Run architecture checks through Make, full static checks and frontend build.
Inspect existing source findings and preserve legitimate schema/type imports.
Keep existing automated tests in PR CI; no new/local tests requested for this task.

# Impact

New forbidden dependencies fail make check and the existing required CI jobs.
Static dependency checks do not prove business design or arbitrary runtime call paths.

# Loop Alignment

Request lifecycle and frontend API state ownership are enforced at dependency boundaries.
Domain events, background execution, realtime, connectivity and visual composition
behavior are unchanged; showcase coverage is outside this task.

# Verification

- make architecture-check and make check passed against existing source.
- B4React make check/build passed; no existing explicit boundary violations found.
- B4React PR #2 passed Frontend checks/Git governance and merged as b71245e; parent pins it.
- Local/new tests were not requested and were not run/added; existing PR CI tests remain enabled.
- Staged governance check required before commit.
