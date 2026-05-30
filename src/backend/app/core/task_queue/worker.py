import asyncio
import contextlib
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from app.core.cache.redis import RedisManager
from app.core.observability.logging import get_logger

logger = get_logger("app.core.task_queue.worker")

TaskPayload = dict[str, object]
TaskEnvelope = dict[str, object]
TaskHandler = Callable[[TaskPayload], Awaitable[None]]


@dataclass(frozen=True)
class TaskQueueConfig:
    queue_key: str
    dlq_key: str
    block_timeout_seconds: int
    max_retries: int
    retry_delay_seconds: int


@dataclass(frozen=True)
class TaskLifecycleEvent:
    phase: str
    worker_name: str
    task_id: str
    task_type: str
    attempt: int
    payload: TaskPayload
    queue_key: str
    dlq_key: str
    trace_id: str = ""


class TaskQueueObserver(Protocol):
    async def on_event(self, event: TaskLifecycleEvent) -> None: ...


class RedisTaskQueueWorker:
    def __init__(self, *, name: str, config: TaskQueueConfig):
        self._name = name
        self._config = config
        self._handlers: dict[str, TaskHandler] = {}
        self._observers: list[TaskQueueObserver] = []
        self._worker_task: asyncio.Task[None] | None = None
        self._running = False

    def register_handler(self, task_type: str, handler: TaskHandler) -> None:
        self._handlers[task_type] = handler

    def register_observer(self, observer: TaskQueueObserver) -> None:
        self._observers.append(observer)

    async def start(self) -> None:
        if self._worker_task is not None:
            return
        self._running = True
        task_name = f"{self._name}-queue-worker"
        self._worker_task = asyncio.create_task(self._worker_loop(), name=task_name)
        logger.info("Task queue worker started (name=%s).", self._name)

    async def stop(self) -> None:
        self._running = False
        if self._worker_task is None:
            return
        self._worker_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._worker_task
        self._worker_task = None
        logger.info("Task queue worker stopped (name=%s).", self._name)

    async def enqueue(
        self,
        *,
        task_type: str,
        payload: TaskPayload,
        task_id: str | None = None,
        trace_id: str | None = None,
    ) -> None:
        redis = await RedisManager.get_client()
        envelope: TaskEnvelope = {
            "task_id": task_id or str(uuid4()),
            "type": task_type,
            "payload": payload,
            "attempt": 0,
            "created_at": datetime.now(UTC).isoformat(),
            "trace_id": (trace_id or "").strip(),
        }
        await redis.lpush(self._config.queue_key, json.dumps(envelope, separators=(",", ":")))
        await self._publish_event("queued", envelope)
        logger.debug("Task queued (name=%s, type=%s).", self._name, task_type)

    async def _worker_loop(self) -> None:
        redis = await RedisManager.get_client()
        timeout = max(1, self._config.block_timeout_seconds)
        while self._running:
            popped = await redis.brpop(self._config.queue_key, timeout=timeout)
            if popped is None:
                continue
            _queue, raw = popped
            envelope = self._decode_envelope(raw)
            if envelope is None:
                continue
            await self._process_envelope(envelope)

    def _decode_envelope(self, raw_payload: str) -> TaskEnvelope | None:
        try:
            parsed = json.loads(raw_payload)
        except json.JSONDecodeError:
            logger.exception("Task queue payload decode failed (name=%s).", self._name)
            return None
        if not isinstance(parsed, dict):
            logger.warning(
                "Ignoring invalid task payload type (name=%s, payload_type=%s).",
                self._name,
                type(parsed).__name__,
            )
            return None
        return parsed

    async def _process_envelope(self, envelope: TaskEnvelope) -> None:
        task_id = str(envelope.get("task_id", ""))
        task_type = str(envelope.get("type", ""))
        payload = envelope.get("payload")
        attempt = int(envelope.get("attempt", 0))
        if not task_id:
            task_id = str(uuid4())
            envelope["task_id"] = task_id

        if not isinstance(payload, dict):
            logger.warning(
                "Ignoring task without payload object (name=%s, type=%s).",
                self._name,
                task_type,
            )
            return

        handler = self._handlers.get(task_type)
        if handler is None:
            logger.warning(
                "No handler registered for task type (name=%s, type=%s).",
                self._name,
                task_type,
            )
            return

        try:
            await self._publish_event("started", envelope)
            await handler(payload)
            await self._publish_event("succeeded", envelope)
            logger.debug(
                "Task processed (name=%s, type=%s, attempt=%s).",
                self._name,
                task_type,
                attempt,
            )
        except Exception:
            await self._retry_or_dlq(
                envelope=envelope,
                task_type=task_type,
                attempt=attempt,
            )

    async def _retry_or_dlq(
        self,
        *,
        envelope: TaskEnvelope,
        task_type: str,
        attempt: int,
    ) -> None:
        next_attempt = attempt + 1
        max_retries = max(0, self._config.max_retries)
        redis = await RedisManager.get_client()

        if next_attempt > max_retries:
            await redis.lpush(self._config.dlq_key, json.dumps(envelope, separators=(",", ":")))
            await self._publish_event("moved_to_dlq", envelope)
            logger.exception(
                "Task moved to DLQ (name=%s, type=%s, attempt=%s).",
                self._name,
                task_type,
                next_attempt,
            )
            return

        retry_envelope = dict(envelope)
        retry_envelope["attempt"] = next_attempt
        retry_delay = max(0, self._config.retry_delay_seconds)
        if retry_delay > 0:
            await asyncio.sleep(retry_delay)
        await redis.lpush(self._config.queue_key, json.dumps(retry_envelope, separators=(",", ":")))
        await self._publish_event("retry_scheduled", retry_envelope)
        logger.exception(
            "Task retry scheduled (name=%s, type=%s, attempt=%s).",
            self._name,
            task_type,
            next_attempt,
        )

    async def _publish_event(self, phase: str, envelope: TaskEnvelope) -> None:
        if not self._observers:
            return
        payload = envelope.get("payload")
        if not isinstance(payload, dict):
            return

        event = TaskLifecycleEvent(
            phase=phase,
            worker_name=self._name,
            task_id=str(envelope.get("task_id", "")),
            task_type=str(envelope.get("type", "")),
            attempt=int(envelope.get("attempt", 0)),
            payload=payload,
            queue_key=self._config.queue_key,
            dlq_key=self._config.dlq_key,
            trace_id=str(envelope.get("trace_id", "")),
        )
        for observer in self._observers:
            try:
                await observer.on_event(event)
            except Exception:
                logger.exception(
                    "Task queue observer failed (name=%s, phase=%s, type=%s).",
                    self._name,
                    phase,
                    event.task_type,
                )
