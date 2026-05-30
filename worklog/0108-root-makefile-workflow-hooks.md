# Add root Makefile workflow hooks

## Commit Title

Add root Makefile workflow hooks

## Changed File Scope

- Added root-level `Makefile` with backend, frontend, Docker, and aggregate workflow targets.
- Updated root README and Korean README to document Make-based workflows.

## Reason

Developers and coding agents need a single command entry point for common project tasks without manually changing directories or memorizing backend, frontend, and Docker-specific commands.

## Impact

- `make help` lists supported project workflow hooks.
- Backend, frontend, and Docker workflows can be launched from the repository root.
- Existing shell scripts remain available and are wrapped by Make targets where appropriate.

## Verification

- `make help`
- `make backend-check`
