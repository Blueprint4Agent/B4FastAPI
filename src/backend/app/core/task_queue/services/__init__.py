"""Task queue service adapters."""

from app.core.task_queue.bootstrap import TaskQueueBootstrap
from app.core.task_queue.services.mail import MAIL_QUEUE_SERVICE

TASK_QUEUE_BOOTSTRAP = TaskQueueBootstrap(
    services=[
        ("mail", MAIL_QUEUE_SERVICE),
    ]
)

__all__ = ["MAIL_QUEUE_SERVICE", "TASK_QUEUE_BOOTSTRAP"]
