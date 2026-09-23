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
