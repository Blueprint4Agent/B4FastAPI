# commit title
feat(frontend): improve login remember controls

# changed file scope
- src/frontend/src/components/ui/inputs/FormCheckbox.tsx
- src/frontend/src/pages/main/ShowCasePage.tsx
- src/frontend/src/styles/app.css
- src/frontend/src/tests/component/pages/login/LoginPage.test.tsx
- src/frontend/src/tests/integration/hooks/useAuth.test.tsx
- src/frontend/src/tests/unit/utils/apiBase.test.ts
- src/frontend/src/utils/apiBase.ts
- src/frontend/.env.example
- src/frontend/README.md
- src/frontend/TEST.md
- notes/ko/frontend/README.md
- notes/ko/frontend/TEST.md
- worklog/0112-login-remember-checkbox-style.md

# reason
- Login remember controls used browser-default checkbox rendering.
- Remember email and remember-me behavior needed explicit component coverage.
- The checked indicator needed stable visual centering and visible showcase states.
- Tab-close session restoration needed an explicit test scenario.
- Mixed local loopback hosts prevented the persistent refresh cookie from being sent after reopening the app.

# impact
- Shared `FormCheckbox` now renders a consistent custom checkbox indicator.
- The showcase renders interactive checked and unchecked checkbox examples.
- Login tests now cover persistence and restoration for remembered email and remember-me preferences.
- Auth bootstrap coverage confirms that a browser session cookie restores login after a tab closes.
- Local API URLs now stay on the frontend's loopback host, preserving same-site refresh cookies across tab restarts.
