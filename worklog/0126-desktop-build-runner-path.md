# Commit Title

fix(ci): stabilize desktop build runners

# Changed File Scope

- `.github/workflows/desktop-build.yml`
- `src/frontend/scripts/run-tauri.mjs`

# Reason

Scheduled Desktop Build runs were repeatedly failing on Windows because the Tauri npm shim could not resolve `node` when launched through the Windows shell, and macOS Intel jobs were stuck waiting on the retired `macos-13` runner label.

# Impact

- Windows desktop builds launch the Tauri CLI through the current Node executable and the package CLI entrypoint instead of relying on the Windows npm shim shell behavior.
- macOS Intel desktop builds use GitHub's current Intel runner label, `macos-15-intel`.
- Frontend runtime loops are not applicable because this change only updates CI and the desktop build helper script.
