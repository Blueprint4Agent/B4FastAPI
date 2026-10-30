# B4React integration

B4FastAPI owns backend code, its OpenAPI export, integrated packaging, and release workflows.
B4React owns frontend source, tests, desktop shell, a pinned contract, and generated types.
`src/frontend` stores one immutable Git commit reference, not copied source.

## Checkout and development

```sh
git clone --recurse-submodules https://github.com/Blueprint4Agent/B4FastAPI.git
# Existing clones, or after changing parent branches:
git submodule update --init --recursive
make install init
```

The submodule is normally detached. For frontend work, create a named branch inside it,
push to B4React and open its PR. Preserve local edits before changing submodule versions.
After the B4React PR merges:

```sh
git -C src/frontend fetch origin
# Replace the placeholder with the reviewed, merged commit:
git -C src/frontend checkout <reviewed-commit-sha>
make verify-plan
make verify
git add src/frontend
```

Commit the gitlink with a parent worklog and open the parent PR. Roll back by reverting
the parent pointer change and initializing submodules again. CI never follows `--remote`.

## Contract update order

1. Change FastAPI declarations and run `make contract-export` in the provider branch.
2. Check compatibility with the pinned consumer using `make contract-check`.
   Unused additions of paths/methods/components may remain provider-only; existing
   operations/components and global fields must remain exact. Existing schema field
   additions are not automatically compatible. See [contract policy](../contracts/README.md).
3. When the frontend adopts an API or existing contracts change, use a B4React branch
   to update its snapshot, immutable provider provenance and generated types/callers.
   Run the child's `make verify-plan` then `make verify`.
4. Merge the child PR first, then update the parent pin and run the parent scoped
   verification. Use VERIFY_BASE for the full branch; integration still owns contracts
   and packaging even when valid child receipts are reused.

Schema compatibility does not replace authentication, error, cookie, redirect,
readiness or SSE behavior review. Other providers own their contract implementation
and dist packaging adapter.

## Build ownership

`make frontend-build` writes only child dist. `make frontend-package` builds and copies
it to `src/backend/app/static/dist`; `make build` includes this integrated packaging.
Docker multi-stage builds perform their own copy. Separate static hosting may deploy
child dist directly with an appropriate API URL and backend CORS/cookie configuration.

## Service layouts

The pinned frontend supports `sidebar` (default), `topnav`, and `focused` (minimal).
Set backend `APP_LAYOUT` to choose the deployment default; `/config.app_layout`
exposes it to the frontend. Recreate the deployed container after an environment
change and reload the browser; the same image supports all three layouts.
`src/frontend/src/service.config.ts` is only a fallback for older/unavailable providers
or invalid remote values. Only server `APP_MODE=development` exposes Settings → Appearance →
Layout as a browser-local preview; production ignores saved previews. Settings/admin
submenus use a boxed contextual column outside the global header when no sidebar is
present. See [English](../src/frontend/notes/layout-modes.md) and
[한국어](../src/frontend/notes/ko/layout-modes.md). No Docker build argument or
frontend rebuild is needed to change the deployment layout.

## Home landing

The home route uses a dedicated landing composition: a responsive introduction and
real demo screenshot preview, feature cards, workflow/use-case sections, persistent section links and grouped
account shortcuts. The selected service layout and auth/role filtering still apply.
The generic MainPageTemplate remains available for settings-style menu pages.
See the child [page-family rules](../src/frontend/notes/page-families.md#home-landing)
and [home/template guide](../src/frontend/notes/main-page-template.md). No new API,
external asset host or deployment variable is required; /about/ remains static.

Topnav and minimal layouts center plain section links in the header; sidebar retains a capsule. Preview images crossfade every six seconds with a visible progress line, including while hovered or focused. Explicit pause, enlargement, offscreen/hidden state and reduced motion suspend rotation. The footer surface spans the main width.
