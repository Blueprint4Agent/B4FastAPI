# commit title

feat(frontend): add optional Tauri desktop shell

# changed file scope

- src/frontend/src-tauri/
- src/frontend/package.json
- src/frontend/package-lock.json
- src/frontend/.prettierignore
- src/frontend/vite.config.ts
- src/frontend/scripts/start-tauri-dev.mjs
- src/frontend/scripts/run-tauri.mjs
- src/frontend/src/utils/apiBase.ts
- src/frontend/src/tests/unit/utils/apiBase.test.ts
- src/frontend/src/utils/desktopRuntime.ts
- src/frontend/src/utils/desktopWindow.ts
- src/frontend/src/components/layout/DesktopTitleBar.tsx
- src/frontend/src/tests/unit/utils/desktopRuntime.test.ts
- src/frontend/src/tests/component/components/layout/DesktopTitleBar.test.tsx
- src/frontend/src/components/layout/AppNavbar.tsx
- src/frontend/src/pages/main/LandingPage.tsx
- src/frontend/src/locales/en.json
- src/frontend/src/locales/ko.json
- src/frontend/src/styles/app.css
- src/frontend/README.md
- src/frontend/FRONTEND.md
- notes/ko/frontend/README.md
- notes/ko/frontend/FRONTEND.md
- src/frontend/TEST.md
- notes/ko/frontend/TEST.md
- README.md
- notes/ko/README.md
- worklog/0113-tauri-desktop-shell.md

# reason

- Users need to choose between the existing browser frontend and an optional desktop runtime.
- The existing frontend build always copied assets into FastAPI and had no desktop shell target.
- Existing terminal sessions may not include Rust's standard `~/.cargo/bin` path, causing Tauri to fail before startup.
- Frontend production dependencies required lockfile refreshes for published React Router advisories.

# impact

- Browser development and builds remain the default behavior.
- The same React application can run through an optional Tauri 2 desktop shell.
- The npm and Make launch paths restore the standard Cargo path for the command without requiring a terminal restart.
- Authentication routes place the shared theme control inside the desktop titlebar and align macOS traffic lights with the navbar center.
- Desktop navbar dimensions are isolated from the browser navbar so each runtime keeps its intended density.
- The desktop navbar uses a compact 36px titlebar layout with controls scaled to prevent overflow.
- Native macOS traffic lights use a screenshot-calibrated vertical inset to align within the 36px navbar.
- The macOS app icon includes platform-safe transparent padding so Dock and Command-Tab sizing matches native applications.
- macOS uses a dedicated versioned ICNS path so development rebuilds do not retain the previous full-bleed icon.
- The flattened macOS ICNS fallback uses Apple-template proportions and a 22.9% enclosure radius instead of the web brand mark's 16.7% radius.
- Desktop navbar surfaces explicitly start native window dragging while preserving interactions on links, buttons, and menus.
- Tauri window controls share an integrated title bar with landing, authentication, and app navigation.
- Tauri reuses an already-running browser development server or starts one when needed.
- Desktop asset builds no longer need to copy output into the FastAPI static directory.
- Deployment signing, installers, updater, and desktop-specific OAuth deep links remain out of scope.
- Offline data caching and synchronization remain separate from the online-first desktop shell.
- The refreshed frontend lockfile reports no production dependency vulnerabilities.
- Cargo outputs, generated Tauri schemas, and unsupported mobile icon sets stay out of version control.
