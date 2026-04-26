# commit title

frontend: default api base to same-origin in static serving mode

# changed file scope

- `src/frontend/src/utils/apiBase.ts`
- `src/frontend/README.md`

# reason

- Static frontend served from `127.0.0.1:8000` still called API at hardcoded `http://localhost:8000`, causing cross-origin requests and CORS preflight failures.

# impact

- Without explicit `VITE_API_BASE_URL`, frontend now uses `window.location.origin`, so static-serving mode keeps same-origin API calls and avoids host mismatch CORS issues.
- Existing deployments can still override API base through `VITE_API_BASE_URL`.
