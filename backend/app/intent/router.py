"""Deterministic intent router for NexaTel."""

from __future__ import annotations

import sqlite3
from typing import Any

from app.handlers.account import get_account_status
from app.handlers.billing import (
    explain_bill_change,
    filter_bills,
    get_average_bill,
    get_bill_breakdown,
    get_bill_comparison,
    get_bill_extreme,
    get_bill_history_for_customer,
    get_bill_trend,
    get_current_bill,
    get_specific_bill,
    get_total_spending,
)
from app.handlers.cross_domain import (
    get_account_attention_summary,
    get_account_plan_status,
    get_bill_payment_explanation,
    get_bill_payment_status,
    get_billing_support_status,
    get_customer_360,
    get_payment_support_status,
    get_plan_usage_status,
)
from app.handlers.devices import (
    filter_devices,
    get_device_count,
    get_device_diagnostic_limitation,
    get_device_extreme,
    get_device_information,
    get_device_summary,
    get_specific_device,
)
from app.handlers.payments import (
    filter_payments,
    get_last_failed_payment,
    get_last_successful_payment,
    get_payment_aggregate,
    get_payment_by_transaction_reference,
    get_payment_history_for_customer,
    get_payment_outstanding,
    get_payment_status,
    get_payment_summary,
    reconcile_bill_payment,
)
from app.handlers.plans import (
    get_current_plan,
    get_plan_renewal,
)
from app.handlers.subscriptions_catalog import (
    get_list_subscriptions,
    get_plan_catalog,
    get_plan_comparison,
)
from app.handlers.billing_extras import (
    get_bill_charge_summary,
    get_projected_bill,
)
from app.handlers.payment_profile import (
    get_account_credits,
    get_payment_profile_status,
)
from app.handlers.support import (
    filter_support_tickets,
    get_customer_support_tickets,
    get_latest_support_ticket_for_customer,
    get_latest_ticket_update,
    get_most_common_support_category,
    get_specific_support_ticket,
    get_support_summary,
    get_support_ticket_count,
    get_support_ticket_updates,
)
from app.handlers.usage import (
    get_data_usage,
    get_usage_average,
    get_usage_comparison,
    get_usage_extreme,
    get_usage_history,
    get_usage_percentage,
    get_usage_remaining,
    get_usage_summary,
    get_usage_trend,
    get_voice_usage,
    get_sms_usage,
)
from app.intent.parameters import (
    normalize_parameters,
    validate_allowed_parameters,
    validate_required_parameters,
)
from app.intent.registry import get_intent_definition
from app.models.domain import (
    CustomerContext,
    Intent,
)
from app.models.llm import LLMIntentResponse
from app.truth.result import (
    TruthResult,
    unsupported_result,
    validation_error_result,
)
from app.utils.errors import ValidationError


HANDLERS = {
    # Account / plan
    "get_account_status": get_account_status,
    "get_current_plan": get_current_plan,
    "get_plan_renewal": get_plan_renewal,
    "get_list_subscriptions": get_list_subscriptions,
    "get_plan_catalog": get_plan_catalog,
    "get_plan_comparison": get_plan_comparison,

    # Phase 1
    "get_data_usage": get_data_usage,
    "get_voice_usage": get_voice_usage,
    "get_sms_usage": get_sms_usage,
    "get_usage_remaining": get_usage_remaining,
    "get_usage_percentage": get_usage_percentage,
    "get_usage_summary": get_usage_summary,
    "get_usage_history": get_usage_history,
    "get_usage_comparison": get_usage_comparison,
    "get_usage_average": get_usage_average,
    "get_usage_extreme": get_usage_extreme,
    "get_usage_trend": get_usage_trend,

    # Phase 2
    "get_current_bill": get_current_bill,
    "get_specific_bill": get_specific_bill,
    "get_bill_history_for_customer": (
        get_bill_history_for_customer
    ),
    "get_bill_breakdown": get_bill_breakdown,
    "get_bill_comparison": get_bill_comparison,
    "explain_bill_change": explain_bill_change,
    "get_total_spending": get_total_spending,
    "get_average_bill": get_average_bill,
    "get_bill_extreme": get_bill_extreme,
    "get_bill_trend": get_bill_trend,
    "filter_bills": filter_bills,
    "get_bill_charge_summary": get_bill_charge_summary,
    "get_projected_bill": get_projected_bill,

    # Phase 3
    "get_payment_status": get_payment_status,
    "get_payment_history_for_customer": (
        get_payment_history_for_customer
    ),
    "filter_payments": filter_payments,
    "get_last_successful_payment": (
        get_last_successful_payment
    ),
    "get_last_failed_payment": (
        get_last_failed_payment
    ),
    "get_payment_by_transaction_reference": (
        get_payment_by_transaction_reference
    ),
    "reconcile_bill_payment": reconcile_bill_payment,
    "get_payment_outstanding": get_payment_outstanding,
    "get_payment_summary": get_payment_summary,
    "get_payment_aggregate": get_payment_aggregate,
    "get_payment_profile_status": get_payment_profile_status,
    "get_account_credits": get_account_credits,

    # Phase 4
    "get_customer_support_tickets": (
        get_customer_support_tickets
    ),
    "get_latest_support_ticket_for_customer": (
        get_latest_support_ticket_for_customer
    ),
    "get_specific_support_ticket": (
        get_specific_support_ticket
    ),
    "filter_support_tickets": filter_support_tickets,
    "get_support_ticket_count": get_support_ticket_count,
    "get_most_common_support_category": (
        get_most_common_support_category
    ),
    "get_support_summary": get_support_summary,
    "get_latest_ticket_update": get_latest_ticket_update,
    "get_support_ticket_updates": get_support_ticket_updates,

    "get_device_information": get_device_information,
    "get_specific_device": get_specific_device,
    "filter_devices": filter_devices,
    "get_device_count": get_device_count,
    "get_device_extreme": get_device_extreme,
    "get_device_summary": get_device_summary,
    "get_device_diagnostic_limitation": (
        get_device_diagnostic_limitation
    ),

    # Phase 5
    "get_plan_usage_status": get_plan_usage_status,
    "get_bill_payment_status": get_bill_payment_status,
    "get_bill_payment_explanation": (
        get_bill_payment_explanation
    ),
    "get_billing_support_status": (
        get_billing_support_status
    ),
    "get_payment_support_status": (
        get_payment_support_status
    ),
    "get_account_plan_status": get_account_plan_status,
    "get_account_attention_summary": (
        get_account_attention_summary
    ),
    # Phase 6
    "get_customer_360": get_customer_360,
}


class IntentRouter:
    """Route structured intents to deterministic backend handlers."""

    def route(
        self,
        *,
        db: sqlite3.Connection,
        customer: CustomerContext,
        intent_response: LLMIntentResponse,
    ) -> TruthResult[Any]:
        intent = intent_response.intent

        if intent == Intent.UNSUPPORTED:
            return unsupported_result(
                message=(
                    intent_response.clarification
                    or (
                        "I can't help with that request "
                        "using the currently supported "
                        "NexaTel capabilities."
                    )
                ),
            )

        try:
            definition = get_intent_definition(
                intent
            )

        except ValueError:
            return unsupported_result(
                message=(
                    "That request is not currently supported."
                ),
            )

        if not definition.handler_name:
            return unsupported_result(
                message=(
                    "That request is not currently supported."
                ),
            )

        handler = HANDLERS.get(
            definition.handler_name
        )

        if handler is None:
            return unsupported_result(
                message=(
                    "That request is not currently supported."
                ),
            )

        try:
            parameters = normalize_parameters(
                intent_response.parameters
            )

            allowed_parameters = (
                definition.required_parameters
                | definition.optional_parameters
            )

            parameters = {
                key: value
                for key, value in parameters.items()
                if key in allowed_parameters
            }

            validate_allowed_parameters(
                intent_parameters=parameters,
                allowed_parameters=allowed_parameters,
            )

            validate_required_parameters(
                intent_parameters=parameters,
                required_parameters=(
                    definition.required_parameters
                ),
            )

        except ValidationError as exc:
            return validation_error_result(
                message=str(exc),
            )

        return handler(
            db,
            customer,
            **parameters,
        )