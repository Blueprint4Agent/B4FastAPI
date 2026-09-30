# Commit Title

fix(auth): stabilize verification and unify account email feedback

# Changed File Scope

Shared backend email builder, atomic verification-token consumption and regression tests, mail brand defaults and env examples, EN/KO backend docs and frontend submodule integration.

# Reason

Deletion code mail bypasses the existing themed email shell. Login recovery placement interrupts input and resend displays untranslated server prose. Concurrent verification requests can both read the token before deletion and replace successful activation with an error.

# Design

Extend the existing email renderer with a code-only content mode using the same brand header, panel and warning/footer styling. Omit CTA and fallback links in code mode. Integrate the child frontend PR after merge. Default EMAIL_BRAND_NAME and direct template defaults become B4A, retaining explicit overrides. Consume verification tokens atomically with Redis WATCH/MULTI to prevent duplicate activation races. No API/schema/queue policy changes.

# Verification Plan

Run root Make verification; reuse unchanged child verification. Test link/escaping contracts and code-only rendering, inspect email previews at mobile/desktop widths, rebuild the running worker image after template changes.

# Impact

Localized visual/copy changes only. Existing codes and account deletion proof remain unchanged. Worker image must be refreshed for new messages to use the template.

# Loop Alignment

Request and domain event loops unchanged. Existing background mail task calls the shared renderer. Child retains API state and UI composition loops; realtime and desktop recovery are not applicable to presentation-only changes.

# Verification

Root make verify-plan and make verify selected backend + full frontend checks and passed. Subsequent backend token/brand changes were validated through the same backend Make group: 119 tests passed, architecture/env/lint/contract checks passed. Child final full Make verification passed, plus final 97 component tests, 69 browser UI cases and six production route cases. Packaging/custom-brand integration passed before the final verification-page-only edit; final production routes, packaging and custom-brand build checks passed for the final child tree. Child PR #30 merged at b8a7ee28f9d59ed741501cd4b8b3430544803a5d; pinned contract check passed. No selected checks omitted; unchanged groups reused after scoped follow-ups.

Concurrent token reproduction fails against the previous implementation and passes against the atomic implementation. Live account 5 was already verified; Redis pending/unacknowledged counts were zero. No live account mutation or real test email was performed.

Korean login recovery and deletion email inspected at 390/1440px; no mail horizontal overflow. Updated running Docker worker reports B4A/shared shell/no links and healthy; host-published probe 47619578-ab60-4aa4-a41e-2a319693c33f completed in the container. The standalone runtime container is retained; no local-only Compose configuration is added.
