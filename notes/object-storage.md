# Object storage providers

Select **local**, **s3**, **r2** or **supabase** with `OBJECT_STORAGE_PROVIDER`.
The three remote choices share an S3 transport, with different defaults and required
settings. Configuration lives in `app/core/config/settings.py`; `.env.example` in
`src/backend` and `docker` contains every key. Existing `.env` files are not rewritten.
This implements the backend foundation for #108. Profile photos still use the
existing API/Base64 storage until domain integration; no new public file API exists.

## Configuration

Restart the API after changing settings. The app validates configuration, creates
one provider during lifespan, exposes it through `get_object_storage` in `app/deps.py`,
and closes it on shutdown or subsequent startup failure. No buckets are created,
no ACL is changed, and remote errors never fall back to local storage. Startup must
pass `check_connection()` before serving: local creates a unique temporary file,
writes/reads its contents and deletes it; remote performs read-only `HeadBucket`.
An INFO log identifies the provider and success; a sanitized ERROR identifies the
provider and normalized failure code, and aborts startup. No endpoint, local path,
credentials or payload is logged. Clients close even when the probe fails.

For S3, HeadBucket requires bucket-level access (typically `s3:ListBucket` in AWS),
separately from GetObject/PutObject/DeleteObject permissions. Bucket probe success
is **not** evidence of object write/delete permission; verify those separately before
rollout. No test object is created remotely. AWS credential resolution may contact
role/metadata endpoints. Non-HTTP workers using the factory directly must explicitly
call `check_connection()` if they need the same startup evidence.

| Variable | Meaning/default |
| --- | --- |
| `OBJECT_STORAGE_PROVIDER` | `local` (default), `s3`, `r2`, `supabase` |
| `OBJECT_STORAGE_LOCAL_ROOT` | Absolute private directory; unset/empty env uses `src/backend/data/object-storage` |
| `OBJECT_STORAGE_MAX_BYTES` | Per put/get limit, 8 MiB default; 1 byte–100 MiB |
| `OBJECT_STORAGE_TIMEOUT_SECONDS` | S3 connect/read timeout, 10 seconds default; 1–120 |
| `OBJECT_STORAGE_S3_BUCKET` | Existing bucket, required for remote providers |
| `OBJECT_STORAGE_S3_ENDPOINT_URL` | Empty for AWS; required for R2/Supabase; no credentials/query/fragment; production requires HTTPS |
| `OBJECT_STORAGE_S3_REGION` | Required for S3/Supabase; R2 uses `auto` |
| `OBJECT_STORAGE_S3_ACCESS_KEY_ID` | Paired with secret; required for R2/Supabase |
| `OBJECT_STORAGE_S3_SECRET_ACCESS_KEY` | Secret, never sent to frontend |
| `OBJECT_STORAGE_S3_SESSION_TOKEN` | Optional AWS temporary token with explicit paired credentials |
| `OBJECT_STORAGE_S3_ADDRESSING_STYLE` | `auto`, `path`, `virtual`; auto resolves to path for R2/Supabase, SDK auto for S3 |

Local (no account required):

```dotenv
OBJECT_STORAGE_PROVIDER=local
OBJECT_STORAGE_LOCAL_ROOT=
```

AWS S3 (role/default SDK credential chain; keys may also be set explicitly):

```dotenv
OBJECT_STORAGE_PROVIDER=s3
OBJECT_STORAGE_S3_BUCKET=my-private-bucket
OBJECT_STORAGE_S3_REGION=ap-northeast-2
OBJECT_STORAGE_S3_ENDPOINT_URL=
OBJECT_STORAGE_S3_ACCESS_KEY_ID=
OBJECT_STORAGE_S3_SECRET_ACCESS_KEY=
OBJECT_STORAGE_S3_SESSION_TOKEN=
```

Cloudflare R2 (account endpoint only, **no bucket path**; a bucket URL is rejected
at startup to prevent the SDK from appending the bucket twice):

```dotenv
OBJECT_STORAGE_PROVIDER=r2
OBJECT_STORAGE_S3_ENDPOINT_URL=https://ACCOUNT_ID.r2.cloudflarestorage.com
OBJECT_STORAGE_S3_BUCKET=my-private-bucket
OBJECT_STORAGE_S3_REGION=auto
OBJECT_STORAGE_S3_ACCESS_KEY_ID=REPLACE_WITH_R2_S3_KEY
OBJECT_STORAGE_S3_SECRET_ACCESS_KEY=REPLACE_WITH_R2_S3_SECRET
```

Supabase Storage:

```dotenv
OBJECT_STORAGE_PROVIDER=supabase
OBJECT_STORAGE_S3_ENDPOINT_URL=https://PROJECT_REF.storage.supabase.co/storage/v1/s3
OBJECT_STORAGE_S3_BUCKET=my-private-bucket
OBJECT_STORAGE_S3_REGION=REPLACE_WITH_PROJECT_S3_REGION
OBJECT_STORAGE_S3_ACCESS_KEY_ID=REPLACE_WITH_SUPABASE_S3_KEY
OBJECT_STORAGE_S3_SECRET_ACCESS_KEY=REPLACE_WITH_SUPABASE_S3_SECRET
```

Copy Supabase's exact endpoint, region and **S3 credentials** from Storage settings;
anon/service-role API keys are not S3 keys. These server credentials must never be
exposed to the browser; domain services enforce per-user access. Use `s3` plus a
custom endpoint for another S3-compatible vendor. HTTP endpoints are allowed only
in development for local emulators. TLS verification remains enabled.

## Contract and ownership

`core/object_storage/base.py` defines `ObjectStorage`, immutable `ObjectMetadata`
(key, byte size, content type), `StoredObject`, and sanitized `StorageError` codes.
Domain service construction can receive `Depends(get_object_storage)`; non-HTTP
workers can use `await create_object_storage(SETTINGS)` with `try/finally close()`.
Do not instantiate provider SDKs in routers or models.

- `put(key, bytes, content_type)` returns metadata and replaces a same-key object.
- `get(key)` returns bounded bytes and metadata; `stat(key)` reads metadata only.
- `check_connection()` performs the startup probe described above.
- `delete(key)` succeeds when the object is already absent. Missing buckets and
  permission failures remain failures. S3 bucket versioning can leave historical
  versions/delete markers: deletion is not a guarantee of physical erasure.
- Keys use a portable ASCII path subset, up to 512 characters. No absolute paths,
  empty/dot segments, backslashes, percent escapes or arbitrary external URLs.
- Content type is a plain MIME type (no parameters), at most 255 characters.
  It is caller metadata, **not** actual image/content validation.
- `NOT_FOUND`, `ACCESS_DENIED`, `UNAVAILABLE`, `TOO_LARGE`, `INVALID_INPUT`,
  `CORRUPT_OBJECT`, `CLOSED` have sanitized messages. Domains translate these into
  their own HTTP error contract; raw SDK errors/body/credentials are not logged here.
- Blocking I/O runs through Starlette's bounded thread pool. Remote calls use
  standard retries, at most three attempts and per-connect/read timeouts, not a
  total operation deadline. Cancellation/timeouts can leave a completed remote
  write; they do not roll back I/O. Same-key races are last completed write wins.
- No transaction with the application DB, listing, multipart streaming, presigned
  URL, public URL, bucket provisioning or ACL interface is added in this phase.
  Private reads must pass through a future authenticated domain endpoint. Do not
  mount the local directory as public static files.

## Local persistence and deployment

Local storage hashes logical keys into flat filenames and stores a versioned
private record (4-byte header length, JSON metadata, then raw bytes) in each file.
A single temporary-file/fsync/atomic-replace operation avoids mismatched sidecars
and partial reads; no Base64 encoding is used. Object reads reject symlinks and
nonregular files. The configured root and parent directories must be controlled by
the operator, never writable by untrusted users. The backend targets macOS/Linux
POSIX filesystems (`O_NOFOLLOW`); hostile shared directories are not supported.
Atomic replacement is not a cross-machine lock or full power-loss durability guarantee.

Docker Compose mounts `object_storage_data` into the API and Celery worker at
`OBJECT_STORAGE_LOCAL_ROOT` (default `/var/lib/b4fastapi/objects`). Both services use
the same private path. Recreating a container preserves the volume; removing volumes
(e.g. `down -v`) removes data. For standalone workers, configure the same absolute
root/mount. A local named volume is host-local, not shared across independent hosts.
Back up this directory/volume separately from the database and restore both together.
Never store uploads in frontend build output or the image's disposable filesystem.

Changing provider/bucket/root **does not migrate objects**. Future domains should
persist stable object keys plus sufficient storage-location identity, not temporary
signed URLs. Profile integration must define image validation, unique keys, DB failure
compensation, concurrent replacement, old-object cleanup, account deletion, and old
Base64/OAuth URL compatibility before switching existing account data.

## Verification and provider limits

Tests use real temporary local directories and botocore Stubber/SDK configuration.
They cover persistence, corruption, path safety, races, limits, error mapping, response
stream closing, provider settings and lifespan/DI cleanup. No live AWS/R2/Supabase
account was used for write/delete tests. A read-only HeadBucket check on the user-configured
R2 bucket passed after removing a duplicated bucket path from the endpoint; running
server logs and `/ping` confirmed recovery. AWS/Supabase live checks remain unrun.
Before rollout, use a dedicated bucket and test put/stat/get/
delete with least-privilege credentials; record results per vendor. Do not treat mock
checks or successful client creation as verified cloud connectivity.

S3 compatibility is a subset, not identical ACL/versioning support. This adapter uses
SigV4 and optional checksum behavior only when required for portability. References:
[AWS SDK configuration](https://docs.aws.amazon.com/boto3/latest/guide/configuration.html),
[R2 compatibility](https://developers.cloudflare.com/r2/api/s3/api/),
[Supabase compatibility](https://supabase.com/docs/guides/storage/s3/compatibility),
[Supabase S3 authentication](https://supabase.com/docs/guides/storage/s3/authentication).

## Profile photo integration

Migration `0015_profile_photo` adds nullable `users.profile_photo` with a unique object
key and a nonsecret location fingerprint. `profile_image_url` becomes a versioned
private API reference for new photos; existing data/OAuth URLs are not rewritten.
Apply `make db-migrate` before rollout. Downgrade clears managed API URLs before
removing the reference column (files remain for operator recovery).

- `PUT /api/v1/auth/me/photo`: authenticated raw binary body, streamed with an 8 MiB
  bound before image decode. Actual PNG/JPEG/WebP/GIF pixels are verified, limited to
  16 million pixels, EXIF orientation applied, resized within 512px, metadata removed,
  and stored as static WebP. Filename and claimed MIME type are not trusted.
- `GET /api/v1/auth/me/photo?version=...`: current owner's photo only, bearer/API-key
  authenticated, binary WebP with private/no-store and nosniff. No bucket credentials
  or public/signed URL is sent to the browser. Old revision requests return 404.
- `DELETE /api/v1/auth/me/photo`: clear reference then best-effort delete. Repeated
  deletion succeeds. Legacy PATCH photo writes (including null) now return 422; use
  the dedicated endpoints. Name/shortcut PATCH and legacy photo display still work.

The frontend uploads bytes through the auth API hook, updates only confirmed account
state, and uses a single account/version-scoped Blob URL for settings/sidebar display.
Logout/replacement revokes it; aborted/late reads cannot replace a different account's
image. Read failure displays initials without signing the user out; account recovery
can retry the read. No permanent storage URL is kept in browser storage; existing
opt-in recent-account thumbnails retain their existing consent/expiry policy.

### Failure policy and alternatives

Use one authoritative storage provider. An automatic local fallback is not a backup:
it creates a second source of truth, host affinity, replay/sync, capacity and deletion
problems. It is intentionally absent; see [AWS on fallback complexity](https://builder.aws.com/content/3EuS9Sakq7L3VLQIF3qzfMfke1Y/avoiding-fallback-in-distributed-systems).
[OWASP upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
supports bounded input, content validation and private storage.

Upload a fresh random key first, compare-and-swap the DB revision, then delete the
previous key. Storage failure preserves the old DB reference. Losing a concurrent
update returns 409 and cleans only the losing upload. DB errors check the current
reference before compensating: an ambiguous successful commit must not delete the
new current image. A lost acknowledgment can return an error after success; reload
reconciles server truth. Cleanup errors log the immutable key and safe error code,
without undoing a committed update. Account deletion returns the final reference
from its transaction so cleanup does not act on a stale pre-deletion snapshot.

Storage switching is detected by the fingerprint; old keys are neither read nor
deleted from the wrong location. Operators must migrate old files or replace photos.
Cleanup is best effort, not a durable outbox: process termination/cancellation or a
prolonged storage/DB outage can leave orphan files. Review cleanup logs and reconcile
unreferenced `profile-photos/` keys against DB references before deleting anything;
never expire the entire prefix. A future durable cleanup queue is justified by
measured orphan volume or deletion SLA, not enabled here. External backup/retention
is separate and provider-specific; configure it independently of request fallback.
Existing bounded SDK retries remain; clients do not repeatedly retry uploads on 503.
Rate limits and aggregate request quotas belong at the deployment ingress when needed.
Startup still fails closed on the configured storage check as requested; an outage
there prevents a restart until storage recovers. A future optional-service degraded
startup policy should be an explicit availability decision.
