from collections import OrderedDict
from collections.abc import Iterable
from typing import Protocol

from app.core.logging import get_logger

logger = get_logger("app.core.task_queue.bootstrap")


class TaskQueueService(Protocol):
    async def start_worker(self) -> None: ...

    async def stop_worker(self) -> None: ...


class TaskQueueBootstrap:
    def __init__(self, services: Iterable[tuple[str, TaskQueueService]] | None = None):
        self._services: OrderedDict[str, TaskQueueService] = OrderedDict()
        for name, service in services or []:
            self.register(name, service)

    def register(self, name: str, service: TaskQueueService) -> None:
        self._services[name] = service

    async def start_all(self) -> None:
        for name, service in self._services.items():
            await service.start_worker()
            logger.info("Task queue service started (name=%s).", name)

    async def stop_all(self) -> None:
        for name, service in reversed(self._services.items()):
            await service.stop_worker()
            logger.info("Task queue service stopped (name=%s).", name)
