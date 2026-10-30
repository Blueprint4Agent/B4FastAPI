---
name: b4-issue
description: Create or update B4FastAPI GitHub issues from existing issue templates, with duplicate checks and evidence-based acceptance criteria.
---

# B4 issue

Resolve the intended repository; a frontend-only issue may belong to B4React.
Read its AGENTS.md and inspect `.github/ISSUE_TEMPLATE/`. Keep the templates as
source of truth for type, title prefix, language, sections and suggested labels.

1. Search existing open and relevant closed issues for the same problem. Inspect
   matches before deciding to create or update; do not reopen or close unrelated issues.
2. Choose the closest bug, feature, backend, frontend or documentation template.
   Read only that template and use its body headings; do not paste YAML frontmatter
   into the issue body. Check which suggested labels actually exist remotely.
3. Describe the observed problem or requested behavior, affected scope and verifiable
   acceptance criteria. For bugs separate reproduction, expected and actual behavior.
   Mark unknown environment facts or causes as unconfirmed rather than inventing them.
   Link supporting files, logs or related issues when available.
4. For a creation/update request, publish within that scope using a structured body
   or UTF-8 `--body-file`. For a draft/review-only request return the prepared text
   without publishing. An issue request alone does not authorize implementation or PRs.
5. Read back the resulting title, body, labels and URL. On an ambiguous API result,
   inspect remote state before retrying to avoid duplicate issues. Report the result.

Do not require a repository commit/worklog for an issue-only action with no file changes.
