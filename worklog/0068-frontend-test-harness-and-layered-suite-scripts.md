# commit title

frontend: add layered test harness, scenario docs, and split test scripts

# changed file scope

- `src/frontend/package.json`
- `src/frontend/package-lock.json`
- `src/frontend/vite.config.ts`
- `src/frontend/playwright.config.ts`
- `src/frontend/FRONTEND.md`
- `src/frontend/README.md`
- `src/frontend/TEST.md`
- `src/frontend/src/tests/setup.ts`
- `src/frontend/src/tests/mocks/handlers.ts`
- `src/frontend/src/tests/mocks/server.ts`
- `src/frontend/src/tests/utils/renderWithRouter.tsx`
- `src/frontend/src/tests/fixtures/fullSystemScenarioData.ts`
- `src/frontend/src/tests/unit/utils/validation.test.ts`
- `src/frontend/src/tests/component/pages/login/LoginPage.test.tsx`
- `src/frontend/src/tests/component/pages/settings/SettingsPage.test.tsx`
- `src/frontend/src/tests/integration/api/configApi.test.ts`
- `src/frontend/src/tests/integration/hooks/useAuth.test.tsx`
- `src/frontend/tests/e2e/auth-smoke.spec.ts`

# reason

- Standardize frontend tests into a de facto layered layout (`unit`, `component`, `integration`, `e2e`) under `src/tests`.
- Align frontend test scenarios with backend auth/api-key seeded flow and make each branch intent readable with Given/When/Then.
- Provide executable test entry points per layer and a single full-matrix command for consistent local/CI runs.

# impact

- Frontend tests are now centralized under `src/frontend/src/tests` with shared fixture/mocks/setup utilities.
- Contributors can run `test:unit`, `test:component`, `test:integration`, or `test:all` depending on scope.
- Documentation now explicitly describes structure, scenario inventory, and command usage for both developers and reviewers.
