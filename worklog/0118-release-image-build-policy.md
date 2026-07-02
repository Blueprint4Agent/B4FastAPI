# Commit Title

ci: publish images only for release or explicit main builds

# Changed File Scope

- GitHub Actions build workflow image build/publish policy.
- Deployment guide and Korean localized deployment guide.

# Reason

Image publishing should not be tied to every `main` merge. Release and tag events should publish
versioned images automatically, while `main` images should only be produced by an explicit manual
request or the configured schedule.

# Impact

- Pull requests and default manual runs validate backend/frontend checks without building Docker images.
- Release published events and `v*` tag pushes build and publish container images.
- Scheduled runs continue publishing the `main` image as `nightly-main`.
- Manual `publish_image=true` runs publish the selected ref image and default to `main` when no ref is supplied.

# Verification

- `make check`
- `make test`
- `git diff --check`
- Ruby YAML parser for `.github/workflows/build.yml`
