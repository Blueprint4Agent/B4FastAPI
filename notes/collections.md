# Search and pagination contract

## Backend usage

Reuse `PageQuery`, `PageSizeQuery`, `SearchQuery` from `app.routers.list_query` in list routers and its `DEFAULT_PAGE_SIZE`:

```python
page: PageQuery = 1,
page_size: PageSizeQuery = DEFAULT_PAGE_SIZE,
search: SearchQuery = "",
```

These are scalar query parameters, not a request body. FastAPI rejects invalid values with 422: page >= 1, page_size 1–100 (default 20), search <= 200 characters. Length validation happens before trimming, preserving the existing contract. Services trim leading/trailing whitespace; an empty search adds no search predicate. Do not silently truncate.

Extend `PageResponse[DomainItemResponse]` for a named domain response; add summary metadata where needed. It supplies `items`, `total`, `page`, `page_size` while preserving the existing admin schema name and flat JSON. Reuse generated frontend types; do not introduce handwritten copies.

Repositories own searchable fields and sorting. For literal substring matching, use `icontains(search, autoescape=True)` as in `Users.list_admin_users` so `%` and `_` are literal, not caller-provided wildcards. Case matching follows the database/collation; do not promise universal Unicode equivalence. Count and rows must use the same authorization/filter predicates. Use deterministic ordering with a unique tie-breaker (admin: descending ID), then offset `(page - 1) * page_size` and limit. Do not load all rows to count or paginate. The count and page are a read-time view, not a transactionally frozen snapshot across requests.

An out-of-range page returns empty `items`, the actual filtered `total` and the requested `page`. The UI may clamp/refetch after success. Empty results are 200, not 404. Keep authorization before list access. Domain summaries may be global; label them separately from filtered total.

Growing collections require server pagination. Cursor pagination needs its own explicit contract and is not provided by these offset helpers. Existing API keys return the complete collection with no count cap; this compatibility exception remains until a separate API migration coordinates provider, pinned consumer contract and generated types.

## Frontend usage

See the pinned [collection guide](../src/frontend/notes/collections.md) and [Korean guide](../src/frontend/notes/ko/collections.md) for `useCollectionQuery`, `useClientPagination`, `getPagination` and wiring examples. Remote queries default to submitted search; local catalogues may search immediately. Applied search/filter/page-size changes return to page 1. Unknown totals must not clamp an in-flight request. Request cancellation, stale-account protection and desktop/realtime recovery remain in domain hooks.

## Verification

Run root `make check` and `make test`. `make contract-check` confirms this extraction does not change the published or pinned OpenAPI schema. Admin integration tests cover defaults, limits, literal search, trimming, authorization and empty/out-of-range results. Frontend tests cover query transitions, local shrinking/reset and existing request/render isolation.
