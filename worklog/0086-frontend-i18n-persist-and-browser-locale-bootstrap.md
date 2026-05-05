# commit title
frontend: persist language selection and bootstrap from browser locale

# changed file scope
- src/frontend/src/i18n.ts

# reason
- Language was resetting to English on page reload because i18n defaulted to fixed `en`.
- Users expect explicit language selection to persist and, without explicit selection, app language to follow browser preference.

# impact
- Selected language now persists via localStorage (`b4a_language`).
- Initial language now resolves in priority order: stored language -> navigator.languages -> navigator.language -> en fallback.
- Reload no longer resets language unexpectedly.
