# commit title
backend: generalize task queue core with bootstrap registry and lifecycle envelope hooks

# changed file scope
- src/backend/app/core/task_queue/worker.py
- src/backend/app/core/task_queue/bootstrap.py
- src/backend/app/core/task_queue/__init__.py
- src/backend/app/core/task_queue/services/__init__.py
- src/backend/app/main.py
- src/backend/BACKEND.md
- docs/ko/backend/BACKEND.md

# reason
- Queue usage was functionally reusable but startup/shutdown orchestration was still mail-service specific in `main.py`.
- Core task envelope lacked generic identifiers and tracing metadata needed for cross-domain observability.
- There was no standardized lifecycle hook interface for future SSE/metrics/audit integrations across multiple queue-backed services.
- Backend architecture docs (EN/KO) needed to reflect the new bootstrap responsibility and structure.

# impact
- Added `TaskQueueBootstrap` to centrally register/start/stop multiple task-queue services.
- Switched application lifespan flow to `TASK_QUEUE_BOOTSTRAP.start_all()` / `stop_all()`, removing direct mail-worker orchestration from `main.py`.
- Extended task envelope with `task_id`, `created_at`, and `trace_id` while preserving existing `type`, `payload`, and `attempt` semantics.
- Added observer contract (`TaskQueueObserver`) and lifecycle event emission points (`queued`, `started`, `succeeded`, `retry_scheduled`, `moved_to_dlq`) in the core worker.
- Updated backend guides in both English and Korean to include task-queue bootstrap placement/rules.
