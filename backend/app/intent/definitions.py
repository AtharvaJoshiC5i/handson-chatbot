"""Definitions of supported NexaTel intents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet

from app.models.domain import Intent


@dataclass(frozen=True)
class IntentDefinition:
    """Metadata describing one supported intent."""

    intent: Intent
    description: str
    required_parameters: FrozenSet[str]
    optional_parameters: FrozenSet[str]
    handler_name: str


INTENT_DEFINITIONS: tuple[IntentDefinition, ...] = (
    IntentDefinition(
        intent=Intent.GET_CURRENT_PLAN,
        description="Retrieve the customer's currently active plan.",
        required_parameters=frozenset(),
        optional_parameters=frozenset(),
        handler_name="get_current_plan",
    ),
    IntentDefinition(
        intent=Intent.GET_ACCOUNT_STATUS,
        description="Retrieve the customer's account status.",
        required_parameters=frozenset(),
        optional_parameters=frozenset(),
        handler_name="get_account_status",
    ),
    IntentDefinition(
        intent=Intent.GET_PLAN_RENEWAL,
        description="Retrieve the customer's next plan renewal date.",
        required_parameters=frozenset(),
        optional_parameters=frozenset(),
        handler_name="get_plan_renewal",
    ),
    IntentDefinition(
        intent=Intent.GET_DATA_USAGE,
        description="Retrieve the customer's data usage.",
        required_parameters=frozenset({"time_range"}),
        optional_parameters=frozenset(),
        handler_name="get_data_usage",
    ),
    IntentDefinition(
        intent=Intent.GET_VOICE_USAGE,
        description="Retrieve the customer's voice usage.",
        required_parameters=frozenset({"time_range"}),
        optional_parameters=frozenset(),
        handler_name="get_voice_usage",
    ),
    IntentDefinition(
        intent=Intent.GET_CURRENT_BILL,
        description="Retrieve the customer's current bill.",
        required_parameters=frozenset(),
        optional_parameters=frozenset(),
        handler_name="get_current_bill",
    ),
    IntentDefinition(
        intent=Intent.GET_BILL_HISTORY,
        description="Retrieve the customer's bill history.",
        required_parameters=frozenset(),
        optional_parameters=frozenset({"limit"}),
        handler_name="get_bill_history_for_customer",
    ),
    IntentDefinition(
        intent=Intent.GET_TOTAL_SPENDING,
        description="Calculate total spending from the customer's bills.",
        required_parameters=frozenset(),
        optional_parameters=frozenset({"limit"}),
        handler_name="get_total_spending",
    ),
    IntentDefinition(
        intent=Intent.GET_BILL_COMPARISON,
        description=(
            "Compare the customer's current and previous bills, "
            "or compare two explicitly identified customer-owned bills."
        ),
        required_parameters=frozenset(),
        optional_parameters=frozenset(
            {
                "current_bill_id",
                "previous_bill_id",
            }
        ),
        handler_name="get_bill_comparison",
    ),
    IntentDefinition(
        intent=Intent.GET_PAYMENT_STATUS,
        description="Retrieve the customer's latest payment status.",
        required_parameters=frozenset(),
        optional_parameters=frozenset(),
        handler_name="get_payment_status",
    ),
    IntentDefinition(
        intent=Intent.GET_PAYMENT_HISTORY,
        description="Retrieve the customer's payment history.",
        required_parameters=frozenset(),
        optional_parameters=frozenset({"limit"}),
        handler_name="get_payment_history_for_customer",
    ),
    IntentDefinition(
        intent=Intent.GET_SUPPORT_TICKETS,
        description="Retrieve the customer's support tickets.",
        required_parameters=frozenset(),
        optional_parameters=frozenset({"limit"}),
        handler_name="get_customer_support_tickets",
    ),
    IntentDefinition(
        intent=Intent.GET_DEVICE_INFORMATION,
        description="Retrieve devices associated with the customer.",
        required_parameters=frozenset(),
        optional_parameters=frozenset(),
        handler_name="get_device_information",
    ),
    IntentDefinition(
        intent=Intent.UNSUPPORTED,
        description=(
            "The user's request is outside the supported "
            "Phase 1 capabilities."
        ),
        required_parameters=frozenset(),
        optional_parameters=frozenset(),
        handler_name="",
    ),
)