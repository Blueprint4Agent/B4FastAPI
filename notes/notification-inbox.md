# Notification inbox

Signed-in users open `/notifications` from the profile menu. Lists, unread filters, pagination and individual/bulk read actions are scoped to the current authenticated user (bearer token or owner API key), including admins. No public demo access or creation endpoint exists.

`inbox_notifications` stores durable user-facing records separately from the mail outbox. Internal producers add records in their domain transaction; email is not required. This PR provides the inbox foundation; inquiry producers are connected in a separate inquiry PR.

After commit, `inbox.changed` SSE invalidates data without broadcasting message content. Reconnect and focus reload authoritative SQL state. Bulk read uses the snapshot high-water ID to preserve newly arriving unread records. Account deletion cascades inbox records. Apply Alembic migrations through 0018 when deploying; container images are not built automatically.

Empty/loading states are centered in a 240px content area, matching the admin collection state. Email and OAuth signup create a welcome record in the same transaction. Confirmed subscription starts and applied plan changes use the validated Stripe webhook, deduplicated by a unique delivery key, even with email disabled. Existing accounts are not backfilled. No browser popup or payment is simulated.
