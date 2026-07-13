# Commit Title

fix(ci): restore desktop build artifact upload

# Changed File Scope

- `.github/workflows/desktop-build.yml`
- `src/frontend/scripts/run-tauri.mjs`

# Reason

The scheduled desktop build failed after Tauri produced bundle paths as a JSON array and `actions/upload-artifact@v7` received that array string as a single path. The Windows desktop build also failed before invoking Tauri because Node attempted to spawn the Windows `.cmd` shim directly.

# Impact

Desktop CI now converts Tauri artifact path output into newline-separated paths before upload. Windows Tauri commands run through the platform shell so the local CLI shim can launch correctly.

# Verification

- `npm run tauri -- --version`
- `make frontend-format-check`
- `make frontend-test`
- `make frontend-desktop-build`
- `git diff --check`
