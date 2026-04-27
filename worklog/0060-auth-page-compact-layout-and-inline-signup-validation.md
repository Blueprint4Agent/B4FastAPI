# 0060 Worklog

- Commit title: `fix: compact auth page layout and move signup required errors inline`
- Scope: `frontend-auth-ui`

## Changed Files

- `src/frontend/src/styles/app.css`
- `src/frontend/src/pages/login/LoginPage.tsx`
- `src/frontend/src/pages/login/SignupPage.tsx`
- `src/frontend/src/pages/login/ForgotPasswordPage.tsx`
- `src/frontend/src/pages/login/ForgotPasswordEmailSentPage.tsx`
- `src/frontend/src/pages/login/ResetPasswordPage.tsx`
- `src/frontend/src/pages/login/ResetPasswordSuccessPage.tsx`
- `src/frontend/src/pages/login/SignupEmailSentPage.tsx`
- `src/frontend/src/pages/login/VerifyEmailPage.tsx`

## Reason

- Reduce the overall visual size of auth pages so cards, inputs, buttons, and feedback blocks feel more compact and aligned.
- Move signup required-field validation from a shared status card to per-field inline messages, matching the input column.

## Impact

- Auth pages now share a tighter visual rhythm with narrower cards, smaller spacing, and smaller supporting UI.
- Signup required-field errors appear directly under each input instead of in a separate status card.
- Feedback alignment is more consistent across auth forms and completion pages.
