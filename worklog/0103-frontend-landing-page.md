# Frontend Landing Page

- commit title: frontend landing page
- changed file scope: frontend routing, landing page UI, i18n copy, localStorage landing state, landing page tests, global styles
- reason: provide a simple customizable template landing page before users enter the auth or showcase flow
- impact: `/` shows the landing page until `b4fastapi:landing:v1:started` is set; the start button routes to `/login` when login is enabled and `/show-case` when login is disabled
