# Support inquiries

Signed-in users open Settings → Support (`/settings?section=support`) to create private text inquiries and read replies. Administrators use `/admin/inquiries` to list all inquiries, reply and set Open, In progress or Closed. Managers have only their own user access. The public admin demo never includes real support data. `/demo/admin/inquiries` reuses this screen with localized synthetic inquiries and replies, no inquiry API reads/writes, and no reply/status actions. It is available only when demo mode is enabled.

API routes live under `/api/v1/inquiries`: list/create, `/{id}` detail, `/{id}/messages` replies, admin-only `/admin` list and `/{id}/status` changes. All reads and responses are no-store. Owner/admin authorization is checked on the server; unrelated IDs return 404. Subject/body limits are 160/4000 characters; threads allow 200 messages. Closed threads reject new replies; admins can reopen them.

Client request UUIDs deduplicate retrying the same create/reply. User/thread locks serialize writes on PostgreSQL. Inquiry changes and inbox entries commit atomically; existing `inbox.changed` SSE carries no content and only refreshes authoritative data. Receipt notifies the owner and active admins; replies notify the other side; status changes notify the owner. Email is not required. There are no attachments or external email forwarding.

Apply migration 0019. Account deletion cascades owned inquiries; deleted administrator identity is removed from retained replies. No container image build is required by the development workflow.

Successful inquiry creation shows the shared confirmation toast. Requesters use “Additional message / Send additional message”; only administrators see “Reply message / Send reply”. Failed sends preserve the draft and do not show success feedback.
