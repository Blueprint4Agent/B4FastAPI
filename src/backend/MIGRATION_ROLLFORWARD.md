# Migration Rollforward Runbook

This runbook defines how to handle migration failures with a rollforward-first policy.
For shared environments and production, do not downgrade by default.

## 1) Preconditions

1. Confirm current target DB and connection settings.
2. Take a DB backup before migration operations.
3. Confirm current revision/head state.

## 2) Baseline Inspection

Run in `src/backend`:

```bash
uv run alembic current
uv run alembic history --verbose
```

## 3) Failure Classification

1. Revision metadata issue:
- Invalid revision naming, broken `down_revision`, duplicated revision.
2. DDL conflict:
- Table/column/index already exists or missing.
3. Data migration issue:
- Constraint/type/length violations.
4. Operational issue:
- Permissions, lock timeout, connectivity.

## 4) Rollforward Procedure

1. Stop automatic deploy retries.
2. Capture failure details:
- failing revision
- SQL/log snippet
- current revision (`alembic current`)
3. Apply forward fix:
- adjust migration logic or add corrective migration revision
4. Re-run:

```bash
uv run alembic upgrade head
```

5. Validate:
- expected schema state
- startup log migration completion
- core API smoke tests

## 5) Guard Rules

1. Revision id format: `NNNN_snake_case`
2. Revision id max length: `32`
3. Never delete already-applied production revisions.
4. Prefer additive and idempotent data migration logic.

## 6) Example: Revision Length Failure

Symptom:
- `value too long for type character varying(32)` on `alembic_version.version_num`.

Action:
1. Shorten offending revision id to 32 chars or less.
2. Update child revision files that reference it in `down_revision`.
3. Rebuild/redeploy and run `alembic upgrade head`.
