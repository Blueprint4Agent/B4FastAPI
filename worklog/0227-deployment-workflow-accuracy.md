# Commit Title

docs(deploy): align deployment instructions with manual workflows

# Changed File Scope

English/Korean deployment and database backup/restore guides.

# Reason

Deployment instructions promise automatic workflows which no longer exist, reference an obsolete macOS runner and hard-code old container names.

# Design

Document actual manual triggers, publishing tags, desktop artifacts, required toolchain and readiness. Use Compose service names for binary-safe database backup/restore. No runtime or schema changes.

# Verification Plan

Root scoped make verify-plan/verify; compare instructions with checked-in workflow/scripts/Compose and check local links. Push hook verifies the complete stacked branch using valid receipts.

# Impact

Documentation-only correction. No workflows are triggered and no database backups/restores or external releases are performed.

# Loop Alignment

Request, event, worker and frontend loops are not applicable to documentation-only changes.

# Verification

- make verify-plan selected full scope because the backend runbook is conservatively classified as an unknown path; no manual downgrade used.
- Default TERM=dumb reproduced the known startup-display fixture failure (449 passed, 1 failed); TERM=xterm-256color make verify then passed the complete required plan.
- Unchanged frontend checks reused matching receipts; contracts/package and branding checks passed. All local links in the four edited guides resolve.
- Triggers, image tags, runners and artifact retention compared with checked-in workflows. No live backup/restore, cloud build or publication was executed.
