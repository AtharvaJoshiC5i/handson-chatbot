"""Definitions of supported NexaTel intents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet

from app.models.domain import Intent


@dataclass(frozen=True)
class IntentDefinition:
    intent: Intent
    description: str
    required_parameters: FrozenSet[str]
    optional_parameters: FrozenSet[str]
    handler_name: str


def _definition(
    intent: Intent,
    handler: str,
    *,
    required=(),
    optional=(),
    description="",
) -> IntentDefinition:
    return IntentDefinition(
        intent=intent,
        description=description,
        required_parameters=frozenset(
            required
        ),
        optional_parameters=frozenset(
            optional
        ),
        handler_name=handler,
    )


PERIOD = (
    "time_range",
    "month",
    "year",
)

PLAN_TYPE = (
    "plan_type",
)


INTENT_DEFINITIONS = (
    # Account / plan
    _definition(
        Intent.GET_CURRENT_PLAN,
        "get_current_plan",
        optional=PLAN_TYPE,
    ),
    _definition(
        Intent.GET_ACCOUNT_STATUS,
        "get_account_status",
    ),
    _definition(
        Intent.GET_PLAN_RENEWAL,
        "get_plan_renewal",
        optional=PLAN_TYPE,
    ),

    _definition(
        Intent.GET_LIST_SUBSCRIPTIONS,
        "get_list_subscriptions",
        optional=(
            *PLAN_TYPE,
            "subscription_status",
        ),
    ),
    _definition(
        Intent.GET_PLAN_CATALOG,
        "get_plan_catalog",
        optional=PLAN_TYPE,
    ),
    _definition(
        Intent.GET_PLAN_COMPARISON,
        "get_plan_comparison",
        required=(
            "plan_id",
            "comparison_plan_id",
        ),
    ),
    _definition(
        Intent.GET_PLAN_DETAILS,
        "get_plan_details",
        required=("plan_id",),
    ),

    _definition(
        Intent.LIST_USAGE_RECORDS,
        "list_usage_records_for_customer",
        optional=(
            "subscription_id",
            "limit",
        ),
    ),
    _definition(
        Intent.LIST_BILL_ITEMS,
        "list_bill_items",
        optional=(
            "current_bill_id",
            "bill_item_type",
            "limit",
        ),
    ),
    _definition(
        Intent.LIST_TICKET_UPDATES,
        "list_ticket_updates",
        optional=(
            "ticket_id",
            "limit",
        ),
    ),


    # Phase 1 — usage
    _definition(
        Intent.GET_DATA_USAGE,
        "get_data_usage",
        optional=(
            *PERIOD,
            *PLAN_TYPE,
        ),
    ),
    _definition(
        Intent.GET_VOICE_USAGE,
        "get_voice_usage",
        optional=(
            *PERIOD,
            *PLAN_TYPE,
        ),
    ),
    _definition(
        Intent.GET_SMS_USAGE,
        "get_sms_usage",
        optional=(
            *PERIOD,
            *PLAN_TYPE,
        ),
    ),
    _definition(
        Intent.GET_USAGE_REMAINING,
        "get_usage_remaining",
        required=(
            "usage_type",
        ),
        optional=PERIOD,
    ),
    _definition(
        Intent.GET_USAGE_PERCENTAGE,
        "get_usage_percentage",
        required=(
            "usage_type",
        ),
        optional=(
            "percentage_type",
            *PERIOD,
        ),
    ),
    _definition(
        Intent.GET_USAGE_SUMMARY,
        "get_usage_summary",
        optional=(
            *PERIOD,
            *PLAN_TYPE,
        ),
    ),
    _definition(
        Intent.GET_USAGE_HISTORY,
        "get_usage_history",
        required=(
            "usage_type",
        ),
        optional=(
            "month_count",
            *PLAN_TYPE,
        ),
    ),
    _definition(
        Intent.GET_USAGE_COMPARISON,
        "get_usage_comparison",
        required=(
            "usage_type",
        ),
        optional=(
            "month",
            "year",
            "comparison_month",
            "comparison_year",
        ),
    ),
    _definition(
        Intent.GET_USAGE_AVERAGE,
        "get_usage_average",
        required=(
            "usage_type",
        ),
        optional=(
            "month_count",
        ),
    ),
    _definition(
        Intent.GET_USAGE_EXTREME,
        "get_usage_extreme",
        required=(
            "usage_type",
            "extreme_type",
        ),
        optional=(
            "month_count",
        ),
    ),
    _definition(
        Intent.GET_USAGE_TREND,
        "get_usage_trend",
        required=(
            "usage_type",
        ),
        optional=(
            "month_count",
        ),
    ),

    # Phase 2 — billing
    _definition(
        Intent.GET_CURRENT_BILL,
        "get_current_bill",
        optional=PLAN_TYPE,
    ),
    _definition(
        Intent.GET_SPECIFIC_BILL,
        "get_specific_bill",
        optional=(
            *PERIOD,
            *PLAN_TYPE,
        ),
    ),
    _definition(
        Intent.GET_BILL_HISTORY,
        "get_bill_history_for_customer",
        optional=(
            "limit",
            *PLAN_TYPE,
        ),
    ),
    _definition(
        Intent.GET_BILL_BREAKDOWN,
        "get_bill_breakdown",
        optional=(
            "month",
            "year",
            "current_bill_id",
        ),
    ),
    _definition(
        Intent.GET_BILL_COMPARISON,
        "get_bill_comparison",
        optional=(
            "current_bill_id",
            "previous_bill_id",
            "month",
            "year",
            "comparison_month",
            "comparison_year",
        ),
    ),
    _definition(
        Intent.EXPLAIN_BILL_CHANGE,
        "explain_bill_change",
        optional=(
            "current_bill_id",
            "previous_bill_id",
            "month",
            "year",
            "comparison_month",
            "comparison_year",
        ),
    ),
    _definition(
        Intent.GET_TOTAL_SPENDING,
        "get_total_spending",
        optional=(
            "limit",
            "month_count",
            "time_range",
        ),
    ),
    _definition(
        Intent.GET_AVERAGE_BILL,
        "get_average_bill",
        optional=(
            "month_count",
        ),
    ),
    _definition(
        Intent.GET_BILL_EXTREME,
        "get_bill_extreme",
        required=(
            "bill_extreme_type",
        ),
        optional=(
            "month_count",
        ),
    ),
    _definition(
        Intent.GET_BILL_TREND,
        "get_bill_trend",
        optional=(
            "month_count",
        ),
    ),
    _definition(
        Intent.FILTER_BILLS,
        "filter_bills",
        optional=(
            "status_filter",
            "minimum_amount",
            "sort_order",
            "limit",
            *PLAN_TYPE,
        ),
    ),
    _definition(
        Intent.GET_BILL_CHARGE_SUMMARY,
        "get_bill_charge_summary",
        required=("bill_item_type",),
        optional=("month_count", *PLAN_TYPE),
    ),
    _definition(
        Intent.GET_PROJECTED_BILL,
        "get_projected_bill",
        optional=PLAN_TYPE,
    ),


    # Phase 3 — payments
    _definition(
        Intent.GET_PAYMENT_STATUS,
        "get_payment_status",
    ),
    _definition(
        Intent.GET_PAYMENT_HISTORY,
        "get_payment_history_for_customer",
        optional=(
            "limit",
            "time_range",
            "month",
            "year",
            "month_count",
        ),
    ),
    _definition(
        Intent.FILTER_PAYMENTS,
        "filter_payments",
        optional=(
            "payment_status",
            "payment_method",
            "limit",
            "time_range",
            "month",
            "year",
            "month_count",
        ),
    ),
    _definition(
        Intent.GET_LAST_SUCCESSFUL_PAYMENT,
        "get_last_successful_payment",
    ),
    _definition(
        Intent.GET_LAST_FAILED_PAYMENT,
        "get_last_failed_payment",
    ),
    _definition(
        Intent.GET_PAYMENT_BY_REFERENCE,
        "get_payment_by_transaction_reference",
        required=(
            "transaction_reference",
        ),
    ),
    _definition(
        Intent.RECONCILE_BILL_PAYMENT,
        "reconcile_bill_payment",
        optional=(
            "month",
            "year",
        ),
    ),
    _definition(
        Intent.GET_PAYMENT_OUTSTANDING,
        "get_payment_outstanding",
        optional=(
            "month",
            "year",
        ),
    ),
    _definition(
        Intent.GET_PAYMENT_SUMMARY,
        "get_payment_summary",
        optional=(
            "month",
            "year",
        ),
    ),
    _definition(
        Intent.GET_PAYMENT_AGGREGATE,
        "get_payment_aggregate",
        required=(
            "payment_aggregate_type",
        ),
        optional=(
            "time_range",
            "month",
            "year",
            "month_count",
        ),
    ),
    _definition(
        Intent.GET_PAYMENT_PROFILE,
        "get_payment_profile_status",
    ),
    _definition(
        Intent.GET_ACCOUNT_CREDITS,
        "get_account_credits",
    ),


    # Phase 4 — support
    _definition(
        Intent.GET_SUPPORT_TICKETS,
        "get_customer_support_tickets",
        optional=(
            "limit",
            "time_range",
            "month_count",
        ),
    ),
    _definition(
        Intent.GET_LATEST_SUPPORT_TICKET,
        "get_latest_support_ticket_for_customer",
    ),
    _definition(
        Intent.GET_SPECIFIC_SUPPORT_TICKET,
        "get_specific_support_ticket",
        required=(
            "ticket_id",
        ),
    ),
    _definition(
        Intent.FILTER_SUPPORT_TICKETS,
        "filter_support_tickets",
        optional=(
            "ticket_status",
            "ticket_priority",
            "ticket_category",
            "unresolved_only",
            "time_range",
            "month_count",
            "limit",
            "support_sort_order",
        ),
    ),
    _definition(
        Intent.GET_SUPPORT_TICKET_COUNT,
        "get_support_ticket_count",
        optional=(
            "ticket_status",
            "ticket_priority",
            "ticket_category",
            "unresolved_only",
            "time_range",
            "month_count",
        ),
    ),
    _definition(
        Intent.GET_SUPPORT_COMMON_CATEGORY,
        "get_most_common_support_category",
    ),
    _definition(
        Intent.GET_SUPPORT_SUMMARY,
        "get_support_summary",
    ),
    _definition(
        Intent.GET_SUPPORT_LAST_UPDATED,
        "get_latest_ticket_update",
        optional=(
            "ticket_id",
        ),
    ),
    _definition(
        Intent.GET_SUPPORT_TICKET_UPDATES,
        "get_support_ticket_updates",
        optional=(
            "ticket_id",
        ),
    ),

    # Phase 4 — devices
    _definition(
        Intent.GET_DEVICE_INFORMATION,
        "get_device_information",
    ),
    _definition(
        Intent.GET_SPECIFIC_DEVICE,
        "get_specific_device",
        required=(
            "device_id",
        ),
    ),
    _definition(
        Intent.FILTER_DEVICES,
        "filter_devices",
        optional=(
            "device_status",
            "device_type",
            "device_sort_order",
            "limit",
        ),
    ),
    _definition(
        Intent.GET_DEVICE_COUNT,
        "get_device_count",
        optional=(
            "device_status",
            "device_type",
        ),
    ),
    _definition(
        Intent.GET_DEVICE_EXTREME,
        "get_device_extreme",
        required=(
            "device_extreme_type",
        ),
    ),
    _definition(
        Intent.GET_DEVICE_SUMMARY,
        "get_device_summary",
    ),
    _definition(
        Intent.GET_DEVICE_DIAGNOSTIC_LIMITATION,
        "get_device_diagnostic_limitation",
    ),

    # ========================================================
    # PHASE 5 — CROSS-DOMAIN
    # ========================================================

    _definition(
        Intent.GET_PLAN_USAGE_STATUS,
        "get_plan_usage_status",
        description=(
            "Compose current plan and current data "
            "allowance usage."
        ),
    ),
    _definition(
        Intent.GET_BILL_PAYMENT_STATUS,
        "get_bill_payment_status",
        description=(
            "Compose current bill and payment "
            "reconciliation."
        ),
    ),
    _definition(
        Intent.GET_BILL_PAYMENT_EXPLANATION,
        "get_bill_payment_explanation",
        description=(
            "Compose current bill items and payment "
            "state."
        ),
    ),
    _definition(
        Intent.GET_BILLING_SUPPORT_STATUS,
        "get_billing_support_status",
        description=(
            "Report billing-category support tickets "
            "without inventing a direct bill link."
        ),
    ),
    _definition(
        Intent.GET_PAYMENT_SUPPORT_STATUS,
        "get_payment_support_status",
        description=(
            "Report payment-category support tickets "
            "without inventing a transaction link."
        ),
    ),
    _definition(
        Intent.GET_ACCOUNT_PLAN_STATUS,
        "get_account_plan_status",
        description=(
            "Compose account, subscription and "
            "current-plan status."
        ),
    ),
    _definition(
        Intent.GET_ACCOUNT_ATTENTION_SUMMARY,
        "get_account_attention_summary",
        description=(
            "Evaluate explicit deterministic account "
            "attention rules."
        ),
    ),
    _definition(
        Intent.GET_CUSTOMER_360,
        "get_customer_360",
        description=(
            "Compose verified account, plan, usage, billing, "
            "payment, support and device information."
        ),
    ),

    _definition(
        Intent.UNSUPPORTED,
        "",
    ),
)