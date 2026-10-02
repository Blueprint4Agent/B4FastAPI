from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.core.error.billing_exception import billing_error_responses
from app.core.error.response_contracts import current_user_error_responses
from app.deps import get_current_user
from app.models.billing import (
    BillingCheckoutForm,
    BillingCheckoutStatusResponse,
    BillingConfigResponse,
    BillingPaymentMethodsResponse,
    BillingPlansResponse,
    BillingSetupForm,
    BillingSetupResponse,
    BillingSetupStatusResponse,
    BillingSubscriptionResponse,
)
from app.models.user import UserResponse
from app.services.billing import BillingService


def no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(
    dependencies=[Depends(no_store)],
    responses=current_user_error_responses(
        billing_error_responses(),
    ),
)


@router.get("/config", response_model=BillingConfigResponse)
async def billing_config(
    current_user: UserResponse = Depends(get_current_user),
    service: BillingService = Depends(BillingService),
) -> BillingConfigResponse:
    return service.config()


@router.post(
    "/setup-sessions", response_model=BillingSetupResponse, status_code=status.HTTP_201_CREATED
)
async def create_setup(
    form: BillingSetupForm,
    current_user: UserResponse = Depends(get_current_user),
    service: BillingService = Depends(BillingService),
) -> BillingSetupResponse:
    return await service.create_setup(current_user.id, form)


@router.get("/setup-sessions/{session_id}", response_model=BillingSetupStatusResponse)
async def setup_status(
    session_id: Annotated[str, Path(pattern=r"^cs_[A-Za-z0-9_]+$", max_length=255)],
    current_user: UserResponse = Depends(get_current_user),
    service: BillingService = Depends(BillingService),
) -> BillingSetupStatusResponse:
    return await service.setup_status(current_user.id, session_id)


@router.get("/payment-methods", response_model=BillingPaymentMethodsResponse)
async def list_payment_methods(
    method_type: Literal["card", "link"] = "card",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    starting_after: Annotated[
        str | None, Query(pattern=r"^pm_[A-Za-z0-9]+$", max_length=255)
    ] = None,
    current_user: UserResponse = Depends(get_current_user),
    service: BillingService = Depends(BillingService),
) -> BillingPaymentMethodsResponse:
    return await service.list_payment_methods(current_user.id, method_type, limit, starting_after)


@router.get("/plans", response_model=BillingPlansResponse)
async def plans(
    current_user: UserResponse = Depends(get_current_user),
    service: BillingService = Depends(BillingService),
) -> BillingPlansResponse:
    return await service.plans()


@router.get("/subscription", response_model=BillingSubscriptionResponse)
async def subscription(
    current_user: UserResponse = Depends(get_current_user),
    service: BillingService = Depends(BillingService),
) -> BillingSubscriptionResponse:
    return await service.subscription(current_user.id)


@router.post(
    "/checkout-sessions", response_model=BillingSetupResponse, status_code=status.HTTP_201_CREATED
)
async def create_checkout(
    form: BillingCheckoutForm,
    current_user: UserResponse = Depends(get_current_user),
    service: BillingService = Depends(BillingService),
) -> BillingSetupResponse:
    return await service.create_checkout(current_user.id, form)


@router.get("/checkout-sessions/{session_id}", response_model=BillingCheckoutStatusResponse)
async def checkout_status(
    session_id: Annotated[str, Path(pattern=r"^cs_[A-Za-z0-9_]+$", max_length=255)],
    current_user: UserResponse = Depends(get_current_user),
    service: BillingService = Depends(BillingService),
) -> BillingCheckoutStatusResponse:
    return await service.checkout_status(current_user.id, session_id)
