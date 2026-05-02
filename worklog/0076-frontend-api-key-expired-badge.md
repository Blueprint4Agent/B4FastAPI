# 0076 frontend api key expired badge

- commit title: frontend: add expired status badge for API keys
- changed file scope:
  - src/frontend/src/components/features/apiKey/DeveloperApiKeysSection.tsx
  - src/frontend/src/utils/date.ts
  - src/frontend/src/locales/en.json
- reason:
  - API key expiration was visible only as date text; status area needed explicit expired signaling.
- impact:
  - API key cards now show `Expired` badge when `expires_at` has passed.
  - Expired detection logic is centralized in date utility for reuse.
  - Locale strings include dedicated expired status label.
