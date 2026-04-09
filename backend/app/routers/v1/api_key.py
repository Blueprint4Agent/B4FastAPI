from fastapi import APIRouter, Depends

from app.core.error import (
    APIKeyErrorCode,
    APIKeyException,
    api_key_error_responses,
    service_exception_to_http,
)
from app.deps import get_current_user
from app.models.api_key import (
    APIKeyCreateForm,
    APIKeyCreateResponse,
    APIKeyResponse,
    APIKeysResponse,
)
from app.models.user import UserResponse
from app.services.api_key import APIKeyService

router = APIRouter()


@router.post(
    "",
    response_model=APIKeyCreateResponse,
    responses=api_key_error_responses(
        APIKeyErrorCode.API_KEY_CREATE_FAILED,
        APIKeyErrorCode.API_KEY_NAME_ALREADY_EXISTS,
    ),
)
async def create_api_key(
    form: APIKeyCreateForm,
    current_user: UserResponse = Depends(get_current_user),
    service: APIKeyService = Depends(APIKeyService),
):
    try:
        return await service.create_api_key(user_id=current_user.id, form=form)
    except APIKeyException as error:
        raise service_exception_to_http(error) from error


@router.get("", response_model=APIKeysResponse)
async def list_api_keys(
    current_user: UserResponse = Depends(get_current_user),
    service: APIKeyService = Depends(APIKeyService),
):
    return await service.list_api_keys(user_id=current_user.id)


@router.delete(
    "/{api_key_id}",
    response_model=APIKeyResponse,
    responses=api_key_error_responses(APIKeyErrorCode.API_KEY_NOT_FOUND),
)
async def revoke_api_key(
    api_key_id: int,
    current_user: UserResponse = Depends(get_current_user),
    service: APIKeyService = Depends(APIKeyService),
):
    try:
        return await service.revoke_api_key(user_id=current_user.id, api_key_id=api_key_id)
    except APIKeyException as error:
        raise service_exception_to_http(error) from error
