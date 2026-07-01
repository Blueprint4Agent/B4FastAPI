# commit title
fix(frontend): keep auth pages scrollable when zoomed

# changed file scope
- src/frontend/src/pages/login/ForgotPasswordEmailSentPage.tsx
- src/frontend/src/pages/login/ForgotPasswordPage.tsx
- src/frontend/src/pages/login/LoginPage.tsx
- src/frontend/src/pages/login/ResetPasswordPage.tsx
- src/frontend/src/pages/login/ResetPasswordSuccessPage.tsx
- src/frontend/src/pages/login/SignupEmailSentPage.tsx
- src/frontend/src/pages/login/SignupPage.tsx
- src/frontend/src/pages/login/VerifyEmailPage.tsx
- src/frontend/src/styles/app.css
- worklog/0110-auth-page-zoom-scroll.md

# reason
- Auth cards can exceed viewport height when users zoom the browser or use a small viewport.
- The global body overflow policy prevents document-level scrolling, so auth pages need their own bounded scroll container.

# impact
- Login, signup, forgot-password, reset-password, and verification pages now scroll within the auth page when content is taller than the viewport.
- Auth cards remain centered when they fit and fall back to safe scrollable positioning when they do not.
