# commit title
docs: move localized docs under docs/<locale> and generalize locale rule

# changed file scope
- README.md
- src/backend/README.md
- src/frontend/README.md
- docs/ko/AGENTS.md
- docs/ko/README.md
- docs/ko/DEPLOY.md
- docs/ko/backend/BACKEND.md
- docs/ko/backend/README.md
- docs/ko/backend/TEST.md
- docs/ko/backend/MIGRATION_ROLLFORWARD.md
- docs/ko/backend/DB_BACKUP_RESTORE.md
- docs/ko/frontend/FRONTEND.md
- docs/ko/frontend/README.md
- docs/ko/frontend/TEST.md

# reason
- Reduce repository clutter from scattered locale-specific markdown files.
- Define a reusable language-agnostic localization convention instead of Korean-only wording.
- Keep translated documentation discoverable with a stable docs/<locale>/ hierarchy.

# impact
- Localized docs are consolidated under docs/ko with backend/frontend domain grouping.
- Core readme entries now describe the generic docs/<locale>/ structure and provide ko as current example.
- Root/backend/frontend quick guides point to locale-structured documentation paths.
