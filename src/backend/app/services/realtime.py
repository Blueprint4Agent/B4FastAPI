from collections.abc import AsyncIterator, Mapping
from enum import StrEnum
from typing import Any

from fastapi import Request

from app.core.realtime.broker import RealtimeBroker
from app.core.realtime.events import build_realtime_event
from app.core.realtime.sse import stream_user_events
from app.models.user import UserResponse


class RealtimeService:
    def stream_user_events(
        self,
        *,
        request: Request,
        current_user: UserResponse,
        last_event_id: str | None,
    ) -> AsyncIterator[str]:
        return stream_user_events(
            request=request,
            current_user=current_user,
            last_event_id=last_event_id,
        )

    async def publish_user_event(
        self,
        *,
        user_id: int,
        event_type: StrEnum | str,
        payload: Mapping[str, Any] | None = None,
    ) -> None:
        event = build_realtime_event(event_type, payload)
        await RealtimeBroker.publish_user_event(user_id=user_id, event=event)
