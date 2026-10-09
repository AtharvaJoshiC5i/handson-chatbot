"""High-confidence routing for the public demo question bank."""

from __future__ import annotations

import re

from app.models.domain import (
    BillExtremeType,
    BillItemType,
    BillStatus,
    DeviceStatus,
    DeviceType,
    Intent,
    PaymentAggregateType,
    PaymentStatus,
    PlanType,
    SupportTicketCategory,
    SupportTicketPriority,
    BillSortOrder,
    TimeRange,
    UsageExtremeType,
    UsagePercentageType,
    UsageType,
)
from app.models.llm import (
    IntentOption,
    IntentParameters,
    LLMIntentResponse,
)

_COUNT_WORDS = {
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "ten": 10,
}


def _extract_count(text: str) -> int | None:
    match = re.search(
        r"\b(?:last|past|recent)\s+"
        r"(\d+|two|three|four|five|six|ten)\b",
        text,
    )
    if match is None:
        match = re.search(
            r"\bfor the last\s+(\d+|ten)\s+days\b",
            text,
        )
    if match is None:
        return None
    value = match.group(1)
    if value in _COUNT_WORDS:
        return _COUNT_WORDS[value]
    return int(value)


def _extract_bill_ids(message: str) -> list[str]:
    return [
        match.group(0).upper()
        for match in re.finditer(
            r"\bBILL[A-Z0-9_-]*\d+[A-Z0-9_-]*\b",
            message,
            flags=re.IGNORECASE,
        )
    ]


def _extract_ticket_id(message: str) -> str | None:
    match = re.search(
        r"\b(?:TICKET|TKT)[A-Z0-9_-]*\d+[A-Z0-9_-]*\b",
        message,
        flags=re.IGNORECASE,
    )
    return match.group(0).upper() if match else None


def _extract_device_id(message: str) -> str | None:
    match = re.search(
        r"\bDEV[A-Z0-9_-]*\d+[A-Z0-9_-]*\b",
        message,
        flags=re.IGNORECASE,
    )
    return match.group(0).upper() if match else None


def _extract_transaction_reference(message: str) -> str | None:
    match = re.search(
        r"\bTXN20\d{6,10}\b",
        message,
        flags=re.IGNORECASE,
    )
    return match.group(0).upper() if match else None


def _extract_amount_threshold(text: str) -> float | None:
    match = re.search(
        r"(?:over|above|more than)\s*₹?\s*([\d,]+(?:\.\d+)?)",
        text,
    )
    if match is None:
        return None
    return float(match.group(1).replace(",", ""))


def _month_from_name(text: str) -> tuple[int | None, int | None]:
    month_map = {
        "january": 1,
        "jan": 1,
        "february": 2,
        "feb": 2,
        "march": 3,
        "mar": 3,
        "april": 4,
        "apr": 4,
        "may": 5,
        "june": 6,
        "jun": 6,
        "july": 7,
        "jul": 7,
        "august": 8,
        "aug": 8,
        "september": 9,
        "sep": 9,
        "sept": 9,
        "october": 10,
        "oct": 10,
        "november": 11,
        "nov": 11,
        "december": 12,
        "dec": 12,
    }
    for name, number in month_map.items():
        if re.search(rf"\b{name}\b", text):
            year_match = re.search(r"\b(20\d{2})\b", text)
            year = int(year_match.group(1)) if year_match else None
            return number, year
    return None, None


def _classify_unsupported_demo(text: str) -> LLMIntentResponse | None:
    if any(
        phrase in text
        for phrase in (
            "cancel my plan",
            "cancel, upgrade, or change my plan",
            "upgrade my plan",
            "change my plan",
            "pay my bill now",
            "pay my bill or recharge",
            "recharge",
            "open or update a support ticket",
            "open a support ticket",
            "update a support ticket",
            "speed test",
            "fix network outage",
            "network outage",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.UNSUPPORTED,
            clarification=(
                "This demo is read-only — I can show your account "
                "data but can't change plans, take payments, or "
                "open or update tickets."
            ),
        )

    if "weather" in text and "mumbai" in text:
        return LLMIntentResponse(
            intent=Intent.UNSUPPORTED,
            clarification=(
                "I can only answer NexaTel account questions for "
                "the customer selected in the app."
            ),
        )

    return None


def _classify_clarifications(text: str) -> LLMIntentResponse | None:
    if text in {
        "how much have i used?",
        "how much have i used",
    }:
        return LLMIntentResponse(
            intent=Intent.UNSUPPORTED,
            clarification=(
                "Do you want data, voice, or SMS usage — and for "
                "this month or a specific period?"
            ),
            options=[
                IntentOption(
                    label="Data this month",
                    message="How much data have I used this month?",
                ),
                IntentOption(
                    label="Voice last month",
                    message="How many voice minutes did I use last month?",
                ),
            ],
        )

    if text in {
        "show my information.",
        "show my information",
    }:
        return LLMIntentResponse(
            intent=Intent.UNSUPPORTED,
            clarification=(
                "Which area should I pull up — plan, usage, bill, "
                "payments, support tickets, or a full account overview?"
            ),
            options=[
                IntentOption(
                    label="Account overview",
                    message="Give me an overview of my account.",
                ),
            ],
        )

    if text in {
        "help with payment.",
        "help with payment",
    }:
        return LLMIntentResponse(
            intent=Intent.UNSUPPORTED,
            clarification=(
                "I can check your latest payment, payment history, "
                "bill payment status, or payment-related support tickets."
            ),
            options=[
                IntentOption(
                    label="Latest payment",
                    message="What is the status of my latest payment?",
                ),
            ],
        )

    if text in {
        "what are my latest details?",
        "what are my latest details",
    }:
        return LLMIntentResponse(
            intent=Intent.UNSUPPORTED,
            clarification=(
                "Latest details for which topic — bill, payment, "
                "usage, or support?"
            ),
        )

    return None


def _classify_account_and_catalog(
    user_message: str,
    text: str,
) -> LLMIntentResponse | None:
    if any(
        phrase in text
        for phrase in (
            "what is my account status",
            "account status",
        )
    ) and "plan" not in text:
        return LLMIntentResponse(
            intent=Intent.GET_ACCOUNT_STATUS,
        )

    if any(
        phrase in text
        for phrase in (
            "active, suspended, or cancelled",
            "suspended or cancelled",
            "account active",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.GET_ACCOUNT_STATUS,
        )

    if "when does my plan renew" in text or "plan renew" in text:
        return LLMIntentResponse(
            intent=Intent.GET_PLAN_RENEWAL,
        )

    if any(
        phrase in text
        for phrase in (
            "check my current plan",
            "what plan and subscription",
            "plan and subscription do i have",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.GET_CURRENT_PLAN,
        )

    if "summary of my account and plan" in text:
        return LLMIntentResponse(
            intent=Intent.GET_ACCOUNT_PLAN_STATUS,
        )

    if "list my subscriptions" in text:
        return LLMIntentResponse(
            intent=Intent.GET_LIST_SUBSCRIPTIONS,
        )

    if "mobile plans are available" in text or "what mobile plans" in text:
        return LLMIntentResponse(
            intent=Intent.GET_PLAN_CATALOG,
            parameters=IntentParameters(
                plan_type=PlanType.MOBILE,
            ),
        )

    if "fiber plans" in text:
        return LLMIntentResponse(
            intent=Intent.GET_PLAN_CATALOG,
            parameters=IntentParameters(
                plan_type=PlanType.FIBER,
            ),
        )

    plan_match = re.search(
        r"\bPLAN[A-Z0-9_-]*\d+[A-Z0-9_-]*\b",
        user_message,
        flags=re.IGNORECASE,
    )
    if plan_match and any(
        phrase in text
        for phrase in (
            "show details",
            "details for plan",
            "plan details",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.GET_PLAN_DETAILS,
            parameters=IntentParameters(
                plan_id=plan_match.group(0).upper(),
            ),
        )

    if "daily usage records" in text or "usage records for" in text:
        parameters = IntentParameters()
        count = _extract_count(text) or 10
        parameters.limit = count
        return LLMIntentResponse(
            intent=Intent.LIST_USAGE_RECORDS,
            parameters=parameters,
        )

    if "bill line items" in text or "line items on my bills" in text:
        return LLMIntentResponse(
            intent=Intent.LIST_BILL_ITEMS,
        )

    if "support ticket updates" in text or "ticket updates" in text:
        return LLMIntentResponse(
            intent=Intent.LIST_TICKET_UPDATES,
        )

    return None


def _classify_bills(
    user_message: str,
    text: str,
) -> LLMIntentResponse | None:
    if "roaming" in text and (
        "spent" in text or "spend" in text
    ):
        return LLMIntentResponse(
            intent=Intent.GET_BILL_CHARGE_SUMMARY,
            parameters=IntentParameters(
                bill_item_type=BillItemType.ROAMING,
                month_count=6,
            ),
        )

    if "bill" not in text and "bills" not in text:
        return None

    bill_ids = _extract_bill_ids(user_message)
    if len(bill_ids) >= 2 and "compare" in text:
        return LLMIntentResponse(
            intent=Intent.GET_BILL_COMPARISON,
            parameters=IntentParameters(
                current_bill_id=bill_ids[0],
                previous_bill_id=bill_ids[1],
            ),
        )

    if len(bill_ids) == 1 and (
        "show bill" in text or bill_ids[0].lower() in text
    ):
        return LLMIntentResponse(
            intent=Intent.GET_BILL_BREAKDOWN,
            parameters=IntentParameters(
                current_bill_id=bill_ids[0],
            ),
        )

    if "what will my bill be" in text or "bill be this month" in text:
        return LLMIntentResponse(
            intent=Intent.GET_PROJECTED_BILL,
        )

    if "break down my bill for september" in text or (
        "break down" in text and "september" in text
    ):
        month, year = _month_from_name(text)
        return LLMIntentResponse(
            intent=Intent.GET_BILL_BREAKDOWN,
            parameters=IntentParameters(
                month=month or 9,
                year=year or 2026,
            ),
        )

    if any(
        phrase in text
        for phrase in (
            "show my latest bill",
            "latest bill",
            "current bill, and when is it due",
            "current bill and when is it due",
        )
    ) and "compare" not in text and "previous" not in text:
        if "due" in text:
            return LLMIntentResponse(
                intent=Intent.GET_CURRENT_BILL,
            )
        return LLMIntentResponse(
            intent=Intent.GET_CURRENT_BILL,
        )

    if "break down my current bill" in text or (
        "break down" in text and "current" in text
    ):
        return LLMIntentResponse(
            intent=Intent.GET_BILL_BREAKDOWN,
        )

    if "last 5 bills" in text or "last five bills" in text:
        return LLMIntentResponse(
            intent=Intent.GET_BILL_HISTORY,
            parameters=IntentParameters(limit=5),
        )

    if "unpaid bills" in text and "newest" in text:
        return LLMIntentResponse(
            intent=Intent.FILTER_BILLS,
            parameters=IntentParameters(
                status_filter=BillStatus.UNPAID,
                sort_order=BillSortOrder.NEWEST,
            ),
        )

    if "spent on my last 3 bills" in text or "last 3 bills" in text:
        return LLMIntentResponse(
            intent=Intent.GET_TOTAL_SPENDING,
            parameters=IntentParameters(limit=3),
        )

    if "average bill" in text:
        return LLMIntentResponse(
            intent=Intent.GET_AVERAGE_BILL,
        )

    if "highest" in text and "bill" in text:
        return LLMIntentResponse(
            intent=Intent.GET_BILL_EXTREME,
            parameters=IntentParameters(
                bill_extreme_type=BillExtremeType.HIGHEST,
                limit=6,
            ),
        )

    if "tax" in text and "bill" in text:
        return LLMIntentResponse(
            intent=Intent.GET_BILL_CHARGE_SUMMARY,
            parameters=IntentParameters(
                bill_item_type=BillItemType.TAX,
            ),
        )

    if "paid bills" in text and "last 6 months" in text:
        return LLMIntentResponse(
            intent=Intent.FILTER_BILLS,
            parameters=IntentParameters(
                status_filter=BillStatus.PAID,
                month_count=6,
            ),
        )

    threshold = _extract_amount_threshold(text)
    if threshold is not None and "bill" in text:
        return LLMIntentResponse(
            intent=Intent.FILTER_BILLS,
            parameters=IntentParameters(
                minimum_amount=threshold,
            ),
        )

    if "bill trend" in text:
        count = _extract_count(text) or 6
        return LLMIntentResponse(
            intent=Intent.GET_BILL_TREND,
            parameters=IntentParameters(limit=count),
        )

    return None


def _classify_payments(
    user_message: str,
    text: str,
) -> LLMIntentResponse | None:
    if "outstanding" in text and "bill" in text:
        return LLMIntentResponse(
            intent=Intent.GET_PAYMENT_OUTSTANDING,
        )

    reference = _extract_transaction_reference(user_message)
    if reference is not None:
        return LLMIntentResponse(
            intent=Intent.GET_PAYMENT_BY_REFERENCE,
            parameters=IntentParameters(
                transaction_reference=reference,
            ),
        )

    if "payment" not in text and "paid" not in text:
        return None

    if any(
        phrase in text
        for phrase in (
            "show my recent payments",
            "show my last 5 payments",
            "last 5 payments",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.GET_PAYMENT_HISTORY,
            parameters=IntentParameters(limit=5),
        )

    if "latest payment" in text and "status" in text:
        return LLMIntentResponse(
            intent=Intent.GET_PAYMENT_STATUS,
        )

    if "gone through" in text or "has my latest payment" in text:
        return LLMIntentResponse(
            intent=Intent.GET_PAYMENT_STATUS,
        )

    if "summarize my payments this year" in text:
        return LLMIntentResponse(
            intent=Intent.GET_PAYMENT_SUMMARY,
            parameters=IntentParameters(
                time_range=TimeRange.CURRENT_YEAR,
            ),
        )

    if "successful this month" in text:
        return LLMIntentResponse(
            intent=Intent.GET_PAYMENT_AGGREGATE,
            parameters=IntentParameters(
                payment_aggregate_type=(
                    PaymentAggregateType.COUNT_SUCCESSFUL
                ),
                time_range=TimeRange.CURRENT_MONTH,
            ),
        )

    if "payment fail" in text or "did my last payment fail" in text:
        return LLMIntentResponse(
            intent=Intent.GET_LAST_FAILED_PAYMENT,
        )

    if "failed payments this year" in text:
        return LLMIntentResponse(
            intent=Intent.FILTER_PAYMENTS,
            parameters=IntentParameters(
                payment_status=PaymentStatus.FAILED,
                time_range=TimeRange.CURRENT_YEAR,
            ),
        )

    if "reconcile my current bill" in text:
        return LLMIntentResponse(
            intent=Intent.RECONCILE_BILL_PAYMENT,
        )

    if (
        "autopay" in text
        or "auto pay" in text
        or "payment method on file" in text
        or "which payment method" in text
    ):
        return LLMIntentResponse(
            intent=Intent.GET_PAYMENT_PROFILE,
        )

    return None


def _classify_support(
    user_message: str,
    text: str,
) -> LLMIntentResponse | None:
    if not any(
        term in text
        for term in ("ticket", "support", "case", "cases")
    ):
        return None

    ticket_id = _extract_ticket_id(user_message)
    if ticket_id and "timeline" in text:
        return LLMIntentResponse(
            intent=Intent.GET_SUPPORT_TICKET_UPDATES,
            parameters=IntentParameters(ticket_id=ticket_id),
        )

    if ticket_id and any(
        phrase in text
        for phrase in ("latest update", "last updated")
    ):
        return LLMIntentResponse(
            intent=Intent.GET_SUPPORT_LAST_UPDATED,
            parameters=IntentParameters(ticket_id=ticket_id),
        )

    if ticket_id:
        return LLMIntentResponse(
            intent=Intent.GET_SPECIFIC_SUPPORT_TICKET,
            parameters=IntentParameters(ticket_id=ticket_id),
        )

    if "summarize my support history" in text:
        return LLMIntentResponse(
            intent=Intent.GET_SUPPORT_SUMMARY,
        )

    if "most common" in text and "category" in text:
        return LLMIntentResponse(
            intent=Intent.GET_SUPPORT_COMMON_CATEGORY,
        )

    if "high-priority billing" in text or (
        "high priority" in text and "billing" in text
    ):
        return LLMIntentResponse(
            intent=Intent.FILTER_SUPPORT_TICKETS,
            parameters=IntentParameters(
                ticket_priority=SupportTicketPriority.HIGH,
                ticket_category=SupportTicketCategory.BILLING,
            ),
        )

    if "billing-related support" in text or (
        "billing-related" in text and "ticket" in text
    ):
        return LLMIntentResponse(
            intent=Intent.GET_BILLING_SUPPORT_STATUS,
        )

    if "payment-related support" in text or (
        "payment-related" in text and "ticket" in text
    ):
        return LLMIntentResponse(
            intent=Intent.GET_PAYMENT_SUPPORT_STATUS,
        )

    return None


def _classify_devices(
    user_message: str,
    text: str,
) -> LLMIntentResponse | None:
    device_id = _extract_device_id(user_message)
    if device_id:
        return LLMIntentResponse(
            intent=Intent.GET_SPECIFIC_DEVICE,
            parameters=IntentParameters(device_id=device_id),
        )

    if "router registered" in text:
        return LLMIntentResponse(
            intent=Intent.FILTER_DEVICES,
            parameters=IntentParameters(
                device_type=DeviceType.ROUTER,
            ),
        )

    if "active phones" in text or "show my active phones" in text:
        return LLMIntentResponse(
            intent=Intent.FILTER_DEVICES,
            parameters=IntentParameters(
                device_type=DeviceType.SMARTPHONE,
                device_status=DeviceStatus.ACTIVE,
            ),
        )

    if "summarize devices" in text:
        return LLMIntentResponse(
            intent=Intent.GET_DEVICE_SUMMARY,
        )

    if "internet slow" in text or "phone internet slow" in text:
        return LLMIntentResponse(
            intent=Intent.GET_DEVICE_DIAGNOSTIC_LIMITATION,
        )

    return None


def _classify_usage_analytics(text: str) -> LLMIntentResponse | None:
    if not any(
        term in text
        for term in ("usage", "data", "voice", "sms", "minutes")
    ):
        return None

    parameters = IntentParameters(usage_type=UsageType.DATA)
    if "voice" in text:
        parameters.usage_type = UsageType.VOICE

    if "average monthly data" in text or "average monthly" in text:
        return LLMIntentResponse(
            intent=Intent.GET_USAGE_AVERAGE,
            parameters=parameters,
        )

    if "highest data" in text:
        return LLMIntentResponse(
            intent=Intent.GET_USAGE_EXTREME,
            parameters=IntentParameters(
                usage_type=UsageType.DATA,
                extreme_type=UsageExtremeType.HIGHEST,
            ),
        )

    if "lowest voice" in text:
        return LLMIntentResponse(
            intent=Intent.GET_USAGE_EXTREME,
            parameters=IntentParameters(
                usage_type=UsageType.VOICE,
                extreme_type=UsageExtremeType.LOWEST,
            ),
        )

    if "data usage trend" in text:
        count = _extract_count(text) or 6
        return LLMIntentResponse(
            intent=Intent.GET_USAGE_TREND,
            parameters=IntentParameters(
                usage_type=UsageType.DATA,
                month_count=count,
            ),
        )

    if "review my data usage" in text:
        return LLMIntentResponse(
            intent=Intent.GET_DATA_USAGE,
            parameters=IntentParameters(
                time_range=TimeRange.CURRENT_MONTH,
            ),
        )

    if "percentage" in text and "allowance" in text:
        return LLMIntentResponse(
            intent=Intent.GET_USAGE_PERCENTAGE,
            parameters=IntentParameters(
                usage_type=UsageType.DATA,
                percentage_type=UsagePercentageType.CONSUMED,
            ),
        )

    if "how many sms" in text:
        return LLMIntentResponse(
            intent=Intent.GET_SMS_USAGE,
            parameters=IntentParameters(
                time_range=TimeRange.CURRENT_MONTH,
            ),
        )

    if "summarize my usage" in text or "summarize all my usage" in text:
        parameters = IntentParameters()
        if "last month" in text:
            parameters.time_range = TimeRange.LAST_MONTH
        else:
            parameters.time_range = TimeRange.CURRENT_MONTH
        return LLMIntentResponse(
            intent=Intent.GET_USAGE_SUMMARY,
            parameters=parameters,
        )

    return None


def _classify_cross_domain(text: str) -> LLMIntentResponse | None:
    if any(
        phrase in text
        for phrase in (
            "need of attention",
            "needs attention",
            "in need of attention",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.GET_ACCOUNT_ATTENTION_SUMMARY,
        )

    if any(
        phrase in text
        for phrase in (
            "overview of my account",
            "give me an overview of my account",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.GET_CUSTOMER_360,
        )

    return None


def classify_demo_question(
    user_message: str,
) -> LLMIntentResponse | None:
    text = user_message.lower().strip()

    blocked = _classify_unsupported_demo(text)
    if blocked is not None:
        return blocked

    clarified = _classify_clarifications(text)
    if clarified is not None:
        return clarified

    for classifier in (
        lambda: _classify_account_and_catalog(
            user_message,
            text,
        ),
        lambda: _classify_cross_domain(text),
        lambda: _classify_bills(user_message, text),
        lambda: _classify_payments(user_message, text),
        lambda: _classify_support(user_message, text),
        lambda: _classify_devices(user_message, text),
        lambda: _classify_usage_analytics(text),
    ):
        response = classifier()
        if response is not None:
            return response

    return None
