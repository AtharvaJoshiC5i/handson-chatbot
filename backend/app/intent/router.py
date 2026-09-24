"""Deterministic routing from validated intents to Python handlers."""

from __future__ import annotations

import sqlite3
from typing import Any, Callable

from app.handlers import (
    get_account_status,
    get_bill_comparison,
    get_current_bill,
    get_current_plan,
    get_customer_support_tickets,
    get_data_usage,
    get_device_information,
    get_payment_history_for_customer,
    get_payment_status,
    get_plan_renewal,
    get_total_spending,
    get_voice_usage,
    get_bill_history_for_customer,
)
from app.intent.parameters import (
    validate_allowed_parameters,
    validate_required_parameters,
)
from app.intent.registry import get_intent_definition
from app.models.domain import CustomerContext, Intent
from app.truth.result import TruthResult, unsupported_result
from app.utils.errors import UnsupportedIntentError


Handler = Callable[..., TruthResult]


HANDLERS: dict[str, Handler] = {
    "get_current_plan": get_current_plan,
    "get_account_status": get_account_status,
    "get_plan_renewal": get_plan_renewal,
    "get_data_usage": get_data_usage,
    "get_voice_usage": get_voice_usage,
    "get_current_bill": get_current_bill,
    "get_bill_history_for_customer": get_bill_history_for_customer,
    "get_total_spending": get_total_spending,
    "get_bill_comparison": get_bill_comparison,
    "get_payment_status": get_payment_status,
    "get_payment_history_for_customer": get_payment_history_for_customer,
    "get_customer_support_tickets": get_customer_support_tickets,
    "get_device_information": get_device_information,
}


class IntentRouter:
    """Route validated intents to known backend handlers."""

    def route(
        self,
        *,
        db: sqlite3.Connection,
        customer: CustomerContext,
        intent: Intent,
        parameters: dict[str, Any],
    ) -> TruthResult:
        """Execute the handler associated with an intent."""

        if intent == Intent.UNSUPPORTED:
            return unsupported_result(
                message=(
                    "This request is outside the currently supported "
                    "NexaTel capabilities."
                )
            )

        definition = get_intent_definition(intent)

        validate_required_parameters(
            intent_parameters=parameters,
            required_parameters=definition.required_parameters,
        )
        validate_allowed_parameters(
            intent_parameters=parameters,
            allowed_parameters=(
                definition.required_parameters
                | definition.optional_parameters
            ),
        )

        handler = HANDLERS.get(
            definition.handler_name
        )

        if handler is None:
            raise UnsupportedIntentError(
                f"No handler is registered for intent: {intent.value}"
            )

        return handler(
            db,
            customer,
            **parameters,
        )