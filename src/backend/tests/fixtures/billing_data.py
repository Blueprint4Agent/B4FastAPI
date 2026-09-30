from types import SimpleNamespace
from unittest.mock import AsyncMock

import stripe

SETUP_REQUEST = {"request_id": "9a3f996f-7e30-4be4-8d74-86f4d8366b29"}


def stripe_object(**values):
    return stripe.StripeObject.construct_from(values, "sk_test_fixture")


def provider_stub():
    return SimpleNamespace(
        v1=SimpleNamespace(
            customers=SimpleNamespace(
                create_async=AsyncMock(return_value=stripe_object(id="cus_fixture")),
                payment_methods=SimpleNamespace(
                    list_async=AsyncMock(return_value=stripe_object(data=[], has_more=False))
                ),
            ),
            checkout=SimpleNamespace(
                sessions=SimpleNamespace(
                    create_async=AsyncMock(
                        return_value=stripe_object(
                            id="cs_test_fixture", url="https://checkout.stripe.com/c/pay/fixture"
                        )
                    ),
                    retrieve_async=AsyncMock(
                        return_value=stripe_object(
                            id="cs_test_fixture",
                            mode="setup",
                            customer="cus_fixture",
                            client_reference_id="1",
                            livemode=False,
                            status="complete",
                            setup_intent={
                                "status": "succeeded",
                                "customer": "cus_fixture",
                                "payment_method": "pm_fixture",
                            },
                        )
                    ),
                )
            ),
        )
    )
