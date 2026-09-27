# Project branding inputs

Optional public SVG/PNG/WEBP/JPEG logos (up to 2 MB each) live here. Reference them
as `"logo": "branding/logo.svg"` and optionally `"logo_dark": "branding/logo-dark.svg"`
in root `project.json`. Keep the assets and manifest in the copied project's Git
repository so CI/Docker builds reproduce its branding. Only trusted public artwork
belongs here; never place credentials in this directory or the manifest.

Web logo/favicon are configured here. Native installer/application icons remain
under B4React `src-tauri/icons`; generating platform icon sets is a separate step.
