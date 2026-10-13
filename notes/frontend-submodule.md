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
make check test build
git add src/frontend
```

Commit the gitlink with a parent worklog and open the parent PR. Roll back by reverting
the parent pointer change and initializing submodules again. CI never follows `--remote`.

## Contract update order

1. Change FastAPI declarations and run `make contract-export` in the provider branch.
2. In a B4React branch, adopt the reviewed snapshot into `contracts/openapi.json`,
   update `contracts/source.json` to its immutable provider source commit, generate
   types, and adapt consumers. Run the child Make checks, tests, and build.
3. Merge B4React first; pin that commit in the provider PR. Run `make check test build`.

The parent semantic JSON equality gate intentionally requires an exact baseline, including
metadata. Additive provider schema changes also require explicit adoption in B4React.
Different backend revisions can use different frontend pins. Schema equality does not
replace authentication, error, cookie, redirect, readiness, and SSE behavior tests.
For Spring Boot, implement the same contract and own its own dist packaging adapter.

## Build ownership

`make frontend-build` writes only child dist. `make frontend-package` builds and copies
it to `src/backend/app/static/dist`; `make build` includes this integrated packaging.
Docker multi-stage builds perform their own copy. Separate static hosting may deploy
child dist directly with an appropriate API URL and backend CORS/cookie configuration.

## Service layouts

The pinned frontend supports `sidebar` (default), `topnav`, and `focused` (minimal).
Set `src/frontend/src/service.config.ts` in the B4React change and rebuild to publish
a service default. Only server `APP_MODE=development` exposes Settings → Appearance →
Layout as a browser-local preview; production ignores saved previews. Settings/admin
submenus use a boxed contextual column outside the global header when no sidebar is
present. See [English](../src/frontend/notes/layout-modes.md) and
[한국어](../src/frontend/notes/ko/layout-modes.md). There are no backend API or Docker
build-argument changes; GHCR uses the source default of its pinned frontend revision.

## Home landing

The home route uses a dedicated landing composition: a responsive introduction and
real demo screenshot preview, plain feature groups, source/guide links and compact
account shortcuts. The selected service layout and auth/role filtering still apply.
The generic MainPageTemplate remains available for settings-style menu pages.
See the child [page-family rules](../src/frontend/notes/page-families.md#home-landing)
and [home/template guide](../src/frontend/notes/main-page-template.md). No new API,
external asset host or deployment variable is required; /about/ remains static.
