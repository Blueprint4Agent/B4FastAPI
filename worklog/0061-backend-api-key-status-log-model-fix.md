# 0061 Worklog

- Commit title: `fix: use api key revoked state in status update logging`
- Scope: `backend-api-key`

## Changed Files

- `src/backend/app/services/api_key.py`

## Reason

- `APIKeyService.update_api_key_status()` logged `updated.enabled`, but `APIKeyResponse` does not expose an `enabled` attribute.
- The mismatch caused an unhandled `AttributeError` during `PATCH /api/v1/api-keys/{id}/status`.

## Impact

- Prevents a 500 error when toggling API key status in the settings UI.
- Keeps status logging aligned with the actual response model by deriving enabled state from `revoked_at`.
