# Commit Title

fix(ci): preserve Windows desktop build path

# Changed File Scope

- `src/frontend/scripts/run-tauri.mjs`

# Reason

The follow-up Desktop Build verification showed Windows now launched Tauri correctly, but Tauri's `beforeBuildCommand` could not find `npm` because the helper rewrote `PATH` instead of preserving Windows' existing `Path` environment key.

# Impact

Windows desktop builds keep the Node and npm directories from the runner environment while still prepending Cargo's bin directory for Tauri. Frontend runtime loops are not applicable because this change only updates the desktop build helper script.
