# Initialize a new project

Use this opt-in workflow after copying the blueprint and initializing its frontend submodule (`make frontend-init`). Install the locked dependencies with `make install`. Existing `make init` remains an env-only workflow.

```sh
cp project.example.json project.json
# Edit the public values in project.json.
make project-plan
make project-init
make project-check
```

`project-plan` validates all inputs and lists affected file paths without writing or printing env values. `project-init` applies the plan, backing up existing changed files under ignored `.project-backups/<timestamp>/`. Repeating it with unchanged inputs makes no changes. `project-check` exits nonzero if generated configuration has drifted; run initialization again to reconcile it. `PROJECT_CONFIG=path/to/project.json make project-init` selects another manifest (logo paths are relative to that manifest). Use root `project.json` for standard CI and Docker builds.

| Field | Effect |
| --- | --- |
| `version` | Manifest format, currently `1` |
| `slug` | Lowercase kebab-case service key; Docker image/Compose project name and telemetry service name |
| `name` | Browser title, public navigation, email brand, API app name, desktop product/window title |
| `short_name` | Shared navbar/sidebar brand wordmark |
| `identifier` | Lowercase reverse-DNS Tauri application ID, e.g. `com.example.myapp` |
| `features.login` | Existing `LOGIN_ENABLED` backend switch |
| `features.email` | Existing `EMAIL_ENABLED` backend switch |
| `features.oauth` | Existing `OAUTH_ENABLED` backend switch |
| `logo`, `logo_dark` | Optional trusted public image paths under `branding/` |

Names accept letters, numbers, spaces and `_ . & ( ) -`, with limits of 60 and 16 characters. Email/OAuth require login. Enabling these switches does not provision email/OAuth providers: configure SMTP, provider credentials and callback URLs separately. Runtime feature visibility continues to come from the backend `/config` endpoint; no feature-setting UI is added.

Optional logo example:

```json
{
  "version": 1,
  "slug": "acme",
  "name": "Acme",
  "short_name": "ACME",
  "identifier": "com.acme.desktop",
  "features": { "login": true, "email": false, "oauth": false },
  "logo": "branding/logo.svg",
  "logo_dark": "branding/logo-dark.svg"
}
```

SVG, PNG, WEBP and JPEG are supported up to 2 MB per file. Without a dark logo the light logo is used in both themes; without a logo the template assets remain. Removing a logo field restores the default reference; obsolete generated image files are not deleted automatically. Tauri installer/native icons remain separate (`src-tauri/icons`). Source npm/Python/Rust package and module names are not renamed.

The initializer owns only identity and the three feature keys in backend/Docker env files. It preserves existing unrelated values, including database connections and configured secrets, and fills missing template defaults. Missing, blank or `CHANGE_ME` secret keys are generated. Frontend `.env` is synchronized from its own example with existing values preserved. No database is contacted or migrated. Changing the Compose project name creates a different resource namespace: use this for a new copied project, not as a running deployment migration.

Commit the public `project.json` and source logos in the copied parent repository. Keep credentials in ignored env files or deployment secret storage. The parent generates ignored `src/frontend/project.local.json` and `src/frontend/public/project-brand/`; do not commit them into the pinned submodule. `make project-brand`, `make frontend-build`, `make frontend-test-routes` and the Docker branding stage regenerate public build inputs without reading secrets. The Docker path uses root `project.json`. Without a root manifest, existing/default frontend identity is kept. Apply `make project-init` after editing features and restart the backend; restart the frontend dev process or rebuild after identity changes.

B4React can also consume its own local public config independently; see its README. Its Vite/Tauri tooling never reads parent files. Use the npm/Make Tauri launcher for identity overrides; invoking the raw Tauri binary bypasses that wrapper.

Validation: `make project-init-check project-init-test` covers initialization and preservation; `make project-build-test` copies the frontend to a temporary directory and verifies a custom Korean/English brand, logo and production browser rendering with the normal frontend Make hooks. The latter requires installed frontend dependencies and Playwright Chromium. Native packaging requires the normal platform toolchain and is not part of that browser check.
