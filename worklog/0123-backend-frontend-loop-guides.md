# Commit Title

docs: define backend and frontend loop checks

# Changed File Scope

- Root agent workflow guide.
- Backend engineering guide and Korean localized backend guide.
- Frontend engineering guide and Korean localized frontend guide.

# Reason

Backend and frontend loop engineering should be explicit when a developer asks for it and should be checked before committing changes. The template needed lightweight runtime loop guidance without expanding into broad planning or review process templates.

# Impact

- Adds a loop check policy for explicit developer requests and pre-commit review.
- Defines backend request lifecycle, domain event, and background task loops.
- Defines frontend API state, realtime refresh, and desktop connectivity recovery loops.
- Keeps localized Korean documentation synchronized with the English guides.

# Verification

- `git diff --check`
- `make check`
- Loop check: documentation-only change; backend and frontend runtime loops are defined, with no runtime implementation loop required.
