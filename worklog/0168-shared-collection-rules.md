# Commit Title

refactor(collections): share search and pagination rules

# Changed File Scope

Backend list schemas/query aliases, admin integration coverage, generic-schema architecture guard and fixtures, Makefile, pinned frontend integration, English/Korean guides.

# Reason

Share list query validation, search submission and page calculations without changing existing API contracts.

# Design

Retain domain-owned filtering, ordering and request hooks. Reuse the existing Pagination and InputField controls. Extract backend query aliases and a generic list response; extract frontend collection query state and local pagination. Keep API key fetching unchanged; server pagination requires a separate contract change. The static architecture guard resolves specialized generic Pydantic inheritance while rejecting Generic-only and repository-mixin classes.

# Verification Plan

Root make check and make test; child make check, make test, make build and make test-ui. Verify unchanged OpenAPI and staged Git governance.

# Impact

No migration or new dependency. Keep existing page sizes and immediate showcase versus submitted admin search. Provide reusable examples in English and Korean.

# Loop Alignment

Request/router/service/repository and frontend page/domain-hook/API loops retained. Existing realtime refresh and desktop recovery remain domain owned. UI composition reuses existing controls. No new domain events or background tasks: this is read-only collection infrastructure.

# Verification

Root make check and make test passed (82 backend tests, 85 frontend tests; initializer checks also passed). OpenAPI and generated types unchanged. Child make check/build and 54 browser UI tests passed. B4React PR #24 merged as cd0e67e954c9a39285904bce25d1ea195e1730db after Git governance and Frontend checks passed (including production routes/style-studio tests). Final root make check/test passed again. Child merge tree matches the locally verified implementation. No required checks skipped.
