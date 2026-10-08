from fastapi import APIRouter, Depends, Response

from app.core.error.admin_exception import AdminErrorCode, admin_error_responses
from app.core.error.auth_exception import AuthErrorCode, auth_error_responses
from app.core.error.response_contracts import current_user_error_responses
from app.core.object_storage import ObjectStorage
from app.deps import get_current_admin_user, get_object_storage
from app.models.admin import AdminStatusResponse
from app.models.user import UserResponse
from app.services.admin import AdminService

router = APIRouter()


@router.get(
    "/status",
    response_model=AdminStatusResponse,
    responses=current_user_error_responses(
        {
            **auth_error_responses(AuthErrorCode.INSUFFICIENT_ROLE),
            **admin_error_responses(AdminErrorCode.STATUS_FAILED),
        }
    ),
)
async def status(
    response: Response,
    current_user: UserResponse = Depends(get_current_admin_user),
    service: AdminService = Depends(AdminService),
    storage: ObjectStorage = Depends(get_object_storage),
) -> AdminStatusResponse:
    response.headers["Cache-Control"] = "no-store"
    return await service.status(storage)
