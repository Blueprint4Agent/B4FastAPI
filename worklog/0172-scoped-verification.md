# Commit Title

ci: select verification by change scope

# Changed File Scope

Scope classifier/runner, regression fixtures, Make targets, CI, agent and bilingual documentation.

# Reason

Reduce redundant validation and logs for low-risk edits while preserving required statuses and governance.

# Design

Use conservative allowlists and structural locale validation; uncertain/protected changes use full checks. Local and CI share one planner. Parent inspects pinned child changes without relying on labels. PR runs cancel superseded runs only.

# Verification Plan

Exercise classifier with real Git fixtures, run planned Make checks for this CI change, validate workflow structure and required status names.

# Impact

Docs/copy avoid dependency install/build/browser checks; runtime retains relevant checks. No runtime app changes.

# Loop Alignment

Application loops unchanged; verification/UI composition and integration contracts remain checked for relevant scope.

# Verification

Root make verify passed the full selected plan: backend lint/architecture/env/contracts and 82 tests; delegated child check/test (93 tests); 65 browser UI cases; 6 production route cases; style-studio checks; contract/package and isolated custom-brand build tests. make verification-test passes 13 cases in each repository, including dirty child files, commit ranges, copy structure, protected/mixed/unknown paths and required workflow names. Ruff and YAML parsing passed. The final packaging optimization was separately verified with make frontend-package-verified; classification/target fixtures protect reuse of route-tested dist. Required governance is validated against staged content before commit. No application checks were skipped for this workflow/tooling change; previously passed delegated checks were not duplicated.

Docs/copy fixtures select zero runtime commands and require no dependency installation. No CI wall-time claim until future low-risk PRs exercise that path. Full logs remain in Git metadata, outside tracked files.

B4React PR #28 merged as 0d8656fcc731c03fedadb7efe539c012aacce88c after required Git governance and Frontend checks passed (full path: 2m48s). MERGE auto-registration was verified. Parent pin now references that merge.
