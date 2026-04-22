# 0056 Worklog

- Commit title: `refactor frontend architecture and component layering`
- Scope: `frontend`

## Changed Files

- `src/frontend/src/pages/*` -> page-group split (`login`, `main`, `settings`)
- `src/frontend/src/components/ui/*` -> category folder split (`buttons/cards/display/dropdowns/inputs/lists/overlays/status/switches/toggles`)
- `src/frontend/src/components/features/*` -> domain feature split (`auth`, `apiKey`)
- `src/frontend/src/api/*` and `src/frontend/src/hooks/api/*` -> domain API and hook structure
- related imports and references in `src/frontend/src/**`

## Reason

- Enforce domain-based frontend architecture.
- Clarify page responsibility vs component responsibility.
- Improve reusability and discoverability of UI primitives.

## Impact

- Stronger separation of concerns: `generated -> api/<domain> -> hooks/api/<domain> -> pages`.
- Components are easier to locate by role (`ui`, `features`, `layout`).
- Build and runtime integration remain intact after structural refactor.
