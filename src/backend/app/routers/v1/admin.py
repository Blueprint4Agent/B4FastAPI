from fastapi import APIRouter, Depends, Response

from app.core.error.admin_exception import AdminErrorCode, admin_error_responses
from app.core.error.auth_exception import AuthErrorCode, auth_error_responses
from app.core.error.response_contracts import current_user_error_responses
from app.core.object_storage import ObjectStorage
from app.deps import get_current_admin_user, get_object_storage
from app.models.admin import AdminStatusResponse
from app.models.user import AdminUserListResponse, UserResponse, UserRole
from app.routers.list_query import DEFAULT_PAGE_SIZE, PageQuery, PageSizeQuery, SearchQuery
from app.services.admin import AdminService, require_demo_enabled

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


@router.get(
    "/demo/users",
    response_model=AdminUserListResponse,
    dependencies=[Depends(require_demo_enabled)],
    responses=admin_error_responses(AdminErrorCode.DEMO_DISABLED, AdminErrorCode.DEMO_FAILED),
)
async def demo_users(
    response: Response,
    page: PageQuery = 1,
    page_size: PageSizeQuery = DEFAULT_PAGE_SIZE,
    search: SearchQuery = "",
    role: UserRole | None = None,
    is_active: bool | None = None,
    service: AdminService = Depends(AdminService),
) -> AdminUserListResponse:
    response.headers["Cache-Control"] = "no-store"
    return await service.demo_users(
        page=page, page_size=page_size, search=search, role=role, is_active=is_active
    )


@router.get(
    "/demo/status",
    response_model=AdminStatusResponse,
    dependencies=[Depends(require_demo_enabled)],
    responses=admin_error_responses(AdminErrorCode.DEMO_DISABLED, AdminErrorCode.DEMO_FAILED),
)
async def demo_status(
    response: Response,
    service: AdminService = Depends(AdminService),
    storage: ObjectStorage = Depends(get_object_storage),
) -> AdminStatusResponse:
    response.headers["Cache-Control"] = "no-store"
    return await service.demo_status(storage)
