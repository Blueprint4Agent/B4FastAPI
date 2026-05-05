from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.error import AuthErrorCode, auth_error_responses
from app.deps import get_current_user
from app.models.user import UserResponse
from app.services.realtime import RealtimeService

router = APIRouter()


@router.get(
    "/stream",
    responses=auth_error_responses(AuthErrorCode.INVALID_TOKEN),
)
async def stream_events(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    service: RealtimeService = Depends(RealtimeService),
) -> StreamingResponse:
    stream = service.stream_user_events(
        request=request,
        current_user=current_user,
        last_event_id=request.headers.get("last-event-id"),
    )
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
