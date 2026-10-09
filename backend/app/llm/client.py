"""Groq LLM client for NexaTel."""

from __future__ import annotations

import json
import re
import time
from calendar import month_abbr, month_name
from collections.abc import Iterator
from typing import Any

from openai import (
    OpenAI,
    RateLimitError,
)

from app.config.settings import Settings
from app.llm.prompts import (
    SYSTEM_PROMPT,
    build_customer_360_response_system_prompt,
    build_response_system_prompt,
)
from app.models.domain import (
    BillStatus,
    DeviceExtremeType,
    DeviceStatus,
    DeviceType,
    Intent,
    PlanType,
    SupportSortOrder,
    SupportTicketCategory,
    SupportTicketPriority,
    SupportTicketStatus,
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
from app.llm.demo_routing import classify_demo_question
from app.utils.errors import LLMError


# ============================================================
# SHARED EXTRACTION HELPERS
# ============================================================


def _extract_count(
    text: str,
) -> int | None:
    words = {
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
    }

    match = re.search(
        r"\b(?:last|past|recent)\s+"
        r"(\d+|three|five|six)\b",
        text,
    )

    if match is None:
        return None

    value = match.group(1)

    if value in words:
        return words[value]

    return int(value)


def _extract_ticket_id(
    user_message: str,
) -> str | None:
    match = re.search(
        r"\b(?:TICKET|TKT)[A-Z0-9_-]*\d+[A-Z0-9_-]*\b",
        user_message,
        flags=re.IGNORECASE,
    )

    if match is None:
        return None

    return (
        match
        .group(0)
        .upper()
    )


def _extract_device_id(
    user_message: str,
) -> str | None:
    match = re.search(
        r"\bDEV[A-Z0-9_-]*\d+[A-Z0-9_-]*\b",
        user_message,
        flags=re.IGNORECASE,
    )

    if match is None:
        return None

    return (
        match
        .group(0)
        .upper()
    )


def _apply_recent_period(
    text: str,
    parameters: IntentParameters,
) -> None:
    count = _extract_count(
        text
    )

    if (
        count is not None
        and "month" in text
    ):
        parameters.month_count = count

    if (
        "last month" in text
        or "previous month" in text
    ):
        parameters.time_range = (
            TimeRange.LAST_MONTH
        )

    elif (
        "this month" in text
        or "current month" in text
    ):
        parameters.time_range = (
            TimeRange.CURRENT_MONTH
        )

    elif (
        "this year" in text
        or "current year" in text
    ):
        parameters.time_range = (
            TimeRange.CURRENT_YEAR
        )


def _usage_clarification_mode(
    text: str,
    parameters: IntentParameters,
) -> str:
    if any(
        term in text
        for term in (
            "compare",
            "comparison",
            "versus",
            " vs ",
            "more than",
            "less than",
        )
    ):
        return "comparison"

    if any(
        term in text
        for term in (
            "remaining",
            "left",
            "balance",
        )
    ):
        return "remaining"

    if "percent" in text or "%" in text:
        return "percentage"

    if "average" in text:
        return "average"

    if "trend" in text:
        return "trend"

    if any(
        term in text
        for term in (
            "highest",
            "most",
            "lowest",
            "least",
        )
    ):
        return "extreme"

    if (
        any(
            term in text
            for term in (
                "history",
                "each month",
                "every month",
                "graph",
                "graphs",
                "chart",
                "charts",
                "plot",
                "visual",
            )
        )
        or parameters.month_count is not None
    ):
        return "history"

    return "current"


def _usage_option_period_clause(
    text: str,
    parameters: IntentParameters,
) -> str:
    if parameters.month_count is not None:
        return (
            f" for the last {parameters.month_count} months"
        )

    if (
        parameters.time_range == TimeRange.LAST_MONTH
        or "last month" in text
    ):
        return " for last month"

    if (
        parameters.time_range == TimeRange.CURRENT_YEAR
        or "this year" in text
        or "current year" in text
    ):
        return " this year"

    if parameters.month is not None:
        month_label = month_name[parameters.month]
        if parameters.year is not None:
            return f" for {month_label} {parameters.year}"
        return f" for {month_label}"

    if (
        parameters.time_range == TimeRange.CURRENT_MONTH
        or "this month" in text
        or "current month" in text
    ):
        return " this month"

    return ""


def _usage_option_message(
    usage_kind: str,
    mode: str,
    period: str,
) -> str:
    if usage_kind == "data":
        if mode == "history":
            return f"Show my data usage{period}."
        if mode == "trend":
            return f"What's my data usage trend{period}?"
        if mode == "comparison":
            return f"Compare my data usage{period}."
        if mode == "remaining":
            return f"How much data do I have left{period}?"
        if mode == "average":
            return f"What's my average monthly data usage{period}?"
        if mode == "percentage":
            return f"What percentage of my data allowance have I used{period}?"
        if mode == "extreme":
            return f"When did I use the most data{period}?"
        return f"How much data have I used{period or ' this month'}?"

    if usage_kind == "voice":
        if mode == "history":
            return f"Show my voice usage{period}."
        if mode == "trend":
            return f"What's my voice usage trend{period}?"
        if mode == "comparison":
            return f"Compare my voice usage{period}."
        if mode == "remaining":
            return f"How many voice minutes do I have left{period}?"
        if mode == "average":
            return f"What's my average monthly voice usage{period}?"
        if mode == "percentage":
            return (
                "What percentage of my voice allowance "
                f"have I used{period}?"
            )
        if mode == "extreme":
            return f"When did I use the most voice minutes{period}?"
        return (
            f"How many voice minutes have I used"
            f"{period or ' this month'}?"
        )

    if mode == "history":
        return f"Show my SMS usage{period}."
    if mode == "trend":
        return f"What's my SMS usage trend{period}?"
    if mode == "comparison":
        return f"Compare my SMS usage{period}."
    if mode == "remaining":
        return f"How many SMS do I have left{period}?"
    if mode == "average":
        return f"What's my average monthly SMS usage{period}?"
    if mode == "percentage":
        return f"What percentage of my SMS allowance have I used{period}?"
    if mode == "extreme":
        return f"When did I send the most SMS{period}?"
    return f"Show my SMS usage{period or ' this month'}."


def _usage_clarification(
    text: str,
    parameters: IntentParameters,
) -> LLMIntentResponse:
    mode = _usage_clarification_mode(
        text,
        parameters,
    )
    period = _usage_option_period_clause(
        text,
        parameters,
    )

    if mode == "history":
        if period:
            clarification = (
                f"Which usage would you like me to show"
                f"{period}: data, voice minutes, or SMS?"
            )
        else:
            clarification = (
                "Which usage history would you like: "
                "data, voice minutes, or SMS?"
            )
    elif mode in {"trend", "comparison", "average", "extreme"}:
        clarification = (
            f"Which usage history should I show{period or ''}: "
            "data, voice minutes, or SMS?"
        )
    elif mode == "remaining":
        clarification = (
            "Which allowance should I check: "
            "data, voice minutes, or SMS?"
        )
    else:
        clarification = (
            "Which usage would you like me to check: "
            "data, voice minutes, or SMS?"
        )

    return LLMIntentResponse(
        intent=Intent.UNSUPPORTED,
        clarification=clarification,
        options=[
            IntentOption(
                label="Data usage",
                message=_usage_option_message(
                    "data",
                    mode,
                    period,
                ),
            ),
            IntentOption(
                label="Voice usage",
                message=_usage_option_message(
                    "voice",
                    mode,
                    period,
                ),
            ),
            IntentOption(
                label="SMS usage",
                message=_usage_option_message(
                    "sms",
                    mode,
                    period,
                ),
            ),
        ],
    )


# ============================================================
# PHASE 5 — CROSS-DOMAIN CLASSIFICATION
# ============================================================


_CUSTOMER_360_PHRASES = (
    "summary of my account",
    "summary of my nexatel account",
    "my account summary",
    "account overview",
    "customer 360",
    "customer360",
    "what's happening with my account",
    "what is happening with my account",
    "summarize my nexatel account",
    "summarize my account",
    "how am i doing overall",
    "entire account information",
    "all my account information",
    "full account information",
    "complete account information",
    "all information about my account",
    "entire information about my account",
    "everything about my account",
    "everything on my account",
    "tell me everything about my account",
    "show me everything about my account",
    "my full profile",
    "my complete profile",
    "all my details",
    "all of my details",
    "full customer profile",
    "comprehensive account view",
    "comprehensive account overview",
    "pull up my full account",
    "show my whole account",
    "what do you know about my account",
    "what do you know about me",
    "give me all my account details",
    "show all my account details",
)

_CUSTOMER_360_PATTERNS = (
    re.compile(
        r"\b(entire|full|complete|all)\s+"
        r"(account\s+)?(profile|information|details|records?|picture|snapshot)\b",
    ),
    re.compile(
        r"\b(show|give|tell|pull\s+up|fetch|get)\s+(me\s+)?"
        r"(my\s+)?(entire|full|complete|all)\s+"
        r"(account|profile|information|details)\b",
    ),
    re.compile(
        r"\beverything\s+(about|on|regarding)\s+"
        r"(my\s+)?(account|profile)\b",
    ),
    re.compile(
        r"\b(all|every)\s+(of\s+)?(my\s+)?"
        r"(account|customer)\s+(details|information|data)\b",
    ),
    re.compile(
        r"\bwhat\s+do\s+you\s+know\s+about\s+(me|my\s+account)\b",
    ),
    re.compile(
        r"\bcomprehensive\s+(view|summary|overview|picture)\b",
    ),
    re.compile(
        r"\bmy\s+whole\s+account\b",
    ),
    re.compile(
        r"\b(entire|full|complete)\s+overview\b",
    ),
)


def _matches_customer_360_request(text: str) -> bool:
    """Holistic account snapshot — not single-domain or attention-only asks."""

    if any(phrase in text for phrase in _CUSTOMER_360_PHRASES):
        return True

    if any(pattern.search(text) for pattern in _CUSTOMER_360_PATTERNS):
        if "attention" in text or "pay attention" in text:
            return False
        if "need to worry" in text:
            return False
        return True

    return False


def classify_phase5_request(
    user_message: str,
) -> LLMIntentResponse | None:
    text = (
        user_message
        .lower()
        .strip()
    )

    parameters = IntentParameters()

    if any(
        phrase in text
        for phrase in (
            "right plan",
            "on the right plan",
            "recommend a plan",
            "better plan for me",
            "should i change my plan",
            "switch my plan",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.GET_PLAN_RECOMMENDATION,
            parameters=parameters,
        )

    if any(
        phrase in text
        for phrase in (
            "bill higher",
            "higher bill",
            "unusually high",
            "why is my bill higher",
            "why is my bill so high",
            "spike in my bill",
            "bill spike",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.GET_BILL_ANOMALY_DETECTION,
            parameters=parameters,
        )

    # --------------------------------------------------------
    # Account attention
    # --------------------------------------------------------

    if any(
        phrase in text
        for phrase in (
            "anything i should pay attention to",
            "anything should i pay attention to",
            "anything on my account need attention",
            "anything on my account needs attention",
            "anything important on my account",
            "account attention summary",
            "anything i should know about my account",
            "anything should i know about my account",
            "what should i know about my account",
            "do i need to worry about anything",
            "anything wrong with my account overall",
            "is anything wrong with my account",
            "does anything need my attention",
            "anything need my attention",
            "what needs my attention",
            "what do i need to pay attention to",
            "is anything pending",
            "anything pending on my account",
            "anything i need to take care of",
            "is there anything i need to take care of",
        )
    ):
        return LLMIntentResponse(
            intent=(
                Intent.GET_ACCOUNT_ATTENTION_SUMMARY
            ),
            parameters=parameters,
        )

    if _matches_customer_360_request(text):
        return LLMIntentResponse(
            intent=Intent.GET_CUSTOMER_360,
            parameters=parameters,
        )

    # --------------------------------------------------------
    # Bill + items + payment
    # --------------------------------------------------------

    has_bill = (
        "bill" in text
        or "billing" in text
        or "charged" in text
        or "charges" in text
    )

    has_payment = (
        "payment" in text
        or (
            "paid" in text
            and "unpaid" not in text
        )
        or "pay " in text
        or "owe" in text
        or (
            "due" in text
            and "overdue" not in text
        )
    )

    has_breakdown = any(
        phrase in text
        for phrase in (
            "break down",
            "breakdown",
            "what am i being charged for",
            "what am i charged for",
            "what makes up",
            "bill charges",
            "charges and payment",
            "explain my current bill",
            "explain my bill",
        )
    )

    if (
        has_bill
        and has_payment
        and has_breakdown
    ):
        return LLMIntentResponse(
            intent=(
                Intent.GET_BILL_PAYMENT_EXPLANATION
            ),
            parameters=parameters,
        )

    # --------------------------------------------------------
    # Bill + payment reconciliation
    # --------------------------------------------------------

    if (
        has_bill
        and has_payment
        and any(
            phrase in text
            for phrase in (
                "did i pay",
                "have i paid",
                "has my bill been paid",
                "has my current bill been paid",
                "bill and payment status",
                "bill with its payment",
                "how much have i paid",
                "how much is left to pay",
                "how much do i still owe",
                "still owe",
                "outstanding on my current bill",
            )
        )
    ):
        return LLMIntentResponse(
            intent=(
                Intent.GET_BILL_PAYMENT_STATUS
            ),
            parameters=parameters,
        )

    # --------------------------------------------------------
    # Billing-category support
    # --------------------------------------------------------

    if (
        (
            "billing" in text
            or "bill" in text
        )
        and (
            "support" in text
            or "ticket" in text
            or "complaint" in text
            or "issue" in text
        )
    ):
        return LLMIntentResponse(
            intent=(
                Intent.GET_BILLING_SUPPORT_STATUS
            ),
            parameters=parameters,
        )

    # --------------------------------------------------------
    # Payment-category support
    # --------------------------------------------------------

    if (
        "payment" in text
        and (
            "support" in text
            or "ticket" in text
            or "complaint" in text
            or "issue" in text
        )
    ):
        return LLMIntentResponse(
            intent=(
                Intent.GET_PAYMENT_SUPPORT_STATUS
            ),
            parameters=parameters,
        )

    # --------------------------------------------------------
    # Plan + usage
    # --------------------------------------------------------

    has_plan = (
        "plan" in text
        or "allowance" in text
        or "data limit" in text
    )

    has_usage = (
        "data" in text
        or "usage" in text
        or "used" in text
        or "remaining" in text
        or "left" in text
        or "limit" in text
    )

    if (
        has_plan
        and has_usage
        and any(
            phrase in text
            for phrase in (
                "how am i doing",
                "close to my",
                "on my current plan",
                "plan and current",
                "plan and usage",
                "using too much",
                "data do i have left",
                "data remaining",
            )
        )
    ):
        return LLMIntentResponse(
            intent=(
                Intent.GET_PLAN_USAGE_STATUS
            ),
            parameters=parameters,
        )

    # --------------------------------------------------------
    # Account + plan / subscription
    # --------------------------------------------------------

    if (
        "account" in text
        and (
            "plan" in text
            or "subscription" in text
        )
        and any(
            phrase in text
            for phrase in (
                "status",
                "active",
                "suspended",
                "anything wrong",
                "show my account",
            )
        )
    ):
        return LLMIntentResponse(
            intent=(
                Intent.GET_ACCOUNT_PLAN_STATUS
            ),
            parameters=parameters,
        )

    return None


# ============================================================
# PHASE 4 — SUPPORT
# ============================================================


def _classify_support_request(
    user_message: str,
    text: str,
) -> LLMIntentResponse | None:
    support_language = any(
        term in text
        for term in (
            "ticket",
            "tickets",
            "support",
            "complaint",
            "complaints",
            "support request",
            "support requests",
            "case",
            "cases",
        )
    )

    if not support_language:
        return None

    parameters = IntentParameters()

    ticket_id = _extract_ticket_id(
        user_message
    )

    if ticket_id is not None:
        parameters.ticket_id = ticket_id

    if any(
        phrase in text
        for phrase in (
            "last updated",
            "latest update",
            "what did support say",
            "what did the agent say",
            "support say",
        )
    ):
        return LLMIntentResponse(
            intent=(
                Intent.GET_SUPPORT_LAST_UPDATED
            ),
            parameters=parameters,
        )

    if ticket_id is not None:
        if any(
            phrase in text
            for phrase in (
                "timeline",
                "full timeline",
                "ticket updates",
            )
        ):
            return LLMIntentResponse(
                intent=Intent.GET_SUPPORT_TICKET_UPDATES,
                parameters=parameters,
            )
        return LLMIntentResponse(
            intent=Intent.GET_SPECIFIC_SUPPORT_TICKET,
            parameters=parameters,
        )

    if any(
        phrase in text
        for phrase in (
            "latest support ticket",
            "latest ticket",
            "most recent ticket",
            "most recent complaint",
            "latest complaint",
            "latest support request",
            "issue did i report most recently",
        )
    ):
        return LLMIntentResponse(
            intent=(
                Intent.GET_LATEST_SUPPORT_TICKET
            ),
            parameters=parameters,
        )

    if (
        "in progress" in text
        or "in-progress" in text
        or "being worked on" in text
    ):
        parameters.ticket_status = (
            SupportTicketStatus.IN_PROGRESS
        )

    elif "resolved" in text:
        parameters.ticket_status = (
            SupportTicketStatus.RESOLVED
        )

    elif "closed" in text:
        parameters.ticket_status = (
            SupportTicketStatus.CLOSED
        )

    elif (
        "open ticket" in text
        or "open tickets" in text
        or "open case" in text
        or "open cases" in text
    ):
        parameters.ticket_status = (
            SupportTicketStatus.OPEN
        )

    if any(
        phrase in text
        for phrase in (
            "unresolved",
            "active support",
            "support issues are currently open",
            "anything with support right now",
            "ongoing support",
        )
    ):
        parameters.unresolved_only = True
        parameters.ticket_status = None

    if (
        "high priority" in text
        or "high-priority" in text
    ):
        parameters.ticket_priority = (
            SupportTicketPriority.HIGH
        )

    elif "critical" in text:
        parameters.ticket_priority = (
            SupportTicketPriority.CRITICAL
        )

    elif "medium priority" in text:
        parameters.ticket_priority = (
            SupportTicketPriority.MEDIUM
        )

    elif "low priority" in text:
        parameters.ticket_priority = (
            SupportTicketPriority.LOW
        )

    if (
        "billing ticket" in text
        or "billing complaint" in text
        or "billing issue" in text
    ):
        parameters.ticket_category = (
            SupportTicketCategory.BILLING
        )

    elif (
        "payment ticket" in text
        or "payment complaint" in text
        or "payment-related" in text
    ):
        parameters.ticket_category = (
            SupportTicketCategory.PAYMENT
        )

    elif (
        "network ticket" in text
        or "network issue" in text
        or "network complaint" in text
    ):
        parameters.ticket_category = (
            SupportTicketCategory.NETWORK
        )

    elif (
        "broadband ticket" in text
        or "broadband issue" in text
    ):
        parameters.ticket_category = (
            SupportTicketCategory.BROADBAND
        )

    elif (
        "plan ticket" in text
        or "plan-related" in text
        or "plan complaint" in text
    ):
        parameters.ticket_category = (
            SupportTicketCategory.PLAN
        )

    _apply_recent_period(
        text,
        parameters,
    )

    count = _extract_count(
        text
    )

    if (
        "how many" in text
        and (
            "ticket" in text
            or "complaint" in text
            or "issue" in text
            or "case" in text
        )
    ):
        parameters.ticket_status = None
        parameters.ticket_priority = None
        parameters.ticket_category = None
        parameters.unresolved_only = None
        if (
            count is not None
            and "month" not in text
        ):
            parameters.limit = count

    if (
        "history" in text
        or "issues have i raised" in text
        or "support requests" in text
        or "tickets" in text
        or "complaints" in text
        or "cases" in text
    ):
        if (
            count is not None
            and "month" not in text
        ):
            parameters.limit = count

        return LLMIntentResponse(
            intent=(
                Intent.GET_SUPPORT_TICKETS
            ),
            parameters=parameters,
        )

    return None


# ============================================================
# PHASE 4 — DEVICES
# ============================================================


def _classify_device_request(
    user_message: str,
    text: str,
) -> LLMIntentResponse | None:
    device_language = any(
        term in text
        for term in (
            "device",
            "devices",
            "router",
            "routers",
            "equipment",
            "modem",
            "modems",
            "tablet",
            "tablets",
            "handset",
            "handsets",
            "registered device",
            "registered devices",
        )
    ) or re.search(
        r"\bdev\d+\b",
        text,
        flags=re.IGNORECASE,
    ) is not None

    if not device_language:
        return None

    parameters = IntentParameters()

    if "router" in text:
        parameters.device_type = DeviceType.ROUTER
    elif "modem" in text:
        parameters.device_type = DeviceType.MODEM
    elif "tablet" in text:
        parameters.device_type = DeviceType.TABLET
    elif any(
        term in text
        for term in (
            "phone",
            "phones",
            "smartphone",
            "handset",
            "handsets",
        )
    ):
        parameters.device_type = DeviceType.SMARTPHONE

    if any(
        phrase in text
        for phrase in (
            "internet slow",
            "slow internet",
            "phone internet slow",
            "why is my phone internet slow",
            "network slow on my phone",
            "diagnose",
            "diagnostics",
            "troubleshoot",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.UNSUPPORTED,
            clarification=(
                "I can list devices registered on your account, but "
                "I can't run network or device diagnostics in this "
                "chat."
            ),
            options=[
                IntentOption(
                    label="Show my devices",
                    message="What devices are on my account?",
                ),
            ],
        )

    return LLMIntentResponse(
        intent=Intent.GET_DEVICE_INFORMATION,
        parameters=parameters,
    )


# ============================================================
# HIGH-CONFIDENCE CLASSIFICATION
# ============================================================


def _classify_general_payment_help(
    text: str,
) -> LLMIntentResponse | None:
    if not any(
        phrase in text
        for phrase in (
            "help with a payment",
            "help with payment",
            "help me with a payment",
            "help me with payment",
            "payment help",
        )
    ):
        return None

    return LLMIntentResponse(
        intent=Intent.UNSUPPORTED,
        clarification=(
            "What would you like help with? I can check your "
            "latest payment, payment history, current bill and "
            "payment status, or payment-related support tickets."
        ),
        options=[
            IntentOption(
                label="Latest payment status",
                message="Has my latest payment gone through?",
            ),
            IntentOption(
                label="Payment history",
                message="Show my payment history.",
            ),
            IntentOption(
                label="Bill and payment status",
                message="What's my current bill and payment status?",
            ),
            IntentOption(
                label="Payment support tickets",
                message="Do I have any support tickets about payments?",
            ),
        ],
    )


def _classify_usage_request(
    text: str,
) -> LLMIntentResponse | None:
    data_terms = ("data", "gb", "gigabyte", "internet")
    voice_terms = ("voice", "call minute", "calling minute", "talk time")
    sms_terms = ("sms", "text message")
    usage_terms = (
        "usage",
        "used",
        "consumed",
        "consumption",
        "allowance",
        "remaining",
        "left",
        "minutes",
    )

    has_usage_language = any(term in text for term in usage_terms) or (
        " use " in f" {text} "
        and any(term in text for term in (*data_terms, *voice_terms, *sms_terms))
    )
    if not has_usage_language:
        return None

    parameters = IntentParameters()
    _apply_recent_period(text, parameters)

    month_pattern = (
        r"\b(january|jan|february|feb|march|mar|april|apr|may|"
        r"june|jun|july|jul|august|aug|september|sept|sep|"
        r"october|oct|november|nov|december|dec)\b"
    )
    named_months = list(re.finditer(month_pattern, text))
    if named_months:
        month_map = {
            month_name[month].lower(): month
            for month in range(1, 13)
        }
        month_map.update(
            {
                month_abbr[month].lower(): month
                for month in range(1, 13)
            }
        )
        filtered_months = [
            match
            for match in named_months
            if match.group(0) != "may"
            or re.search(
                r"\b(?:in|for|during|of|month of)\s+may\b|"
                r"\bmay\s+(?:data|voice|sms|usage|consumption)\b",
                text,
            )
        ]
        if filtered_months:
            parameters.month = month_map[filtered_months[0].group(0)]

            year_match = re.search(r"\b(20\d{2})\b", text)
            if year_match:
                parameters.year = int(year_match.group(1))

            if len(filtered_months) > 1:
                months = sorted(
                    {
                        month_map[match.group(0)]
                        for match in filtered_months[:2]
                    }
                )
                is_range = any(
                    term in text
                    for term in (
                        " from ",
                        " to ",
                        " through ",
                        " until ",
                        " till ",
                        " between ",
                    )
                )
                is_compare = any(
                    term in text
                    for term in (
                        "compare",
                        "comparison",
                        "versus",
                        " vs ",
                        "more than",
                        "less than",
                    )
                )
                if is_range and not is_compare:
                    parameters.month_count = (
                        months[-1] - months[0] + 1
                    )
                    parameters.month = None
                    parameters.comparison_month = None
                elif is_compare:
                    parameters.month = months[-1]
                    parameters.comparison_month = months[0]
                else:
                    parameters.month_count = (
                        months[-1] - months[0] + 1
                    )
                    parameters.month = None
                    parameters.comparison_month = None

    if any(term in text for term in data_terms):
        usage_type = UsageType.DATA
    elif any(term in text for term in voice_terms) or "minutes" in text:
        usage_type = UsageType.VOICE
    elif any(term in text for term in sms_terms):
        usage_type = UsageType.SMS
    else:
        usage_type = None

    if any(
        term in text
        for term in (
            "compare",
            "comparison",
            "versus",
            " vs ",
            "more than",
            "less than",
        )
    ):
        if usage_type is None:
            return _usage_clarification(text, parameters)
        parameters.usage_type = usage_type
        return LLMIntentResponse(
            intent=Intent.GET_USAGE_COMPARISON,
            parameters=parameters,
        )

    if any(term in text for term in ("remaining", "left", "balance")):
        if usage_type is None:
            return _usage_clarification(text, parameters)
        parameters.usage_type = usage_type
        return LLMIntentResponse(
            intent=Intent.GET_USAGE_REMAINING,
            parameters=parameters,
        )

    if "percent" in text or "%" in text:
        if usage_type is None:
            return _usage_clarification(text, parameters)
        parameters.usage_type = usage_type
        parameters.percentage_type = (
            UsagePercentageType.REMAINING
            if "remaining" in text or "left" in text
            else UsagePercentageType.CONSUMED
        )
        return LLMIntentResponse(
            intent=Intent.GET_USAGE_PERCENTAGE,
            parameters=parameters,
        )

    if "trend" in text:
        if usage_type is None:
            return _usage_clarification(text, parameters)
        parameters.usage_type = usage_type
        parameters.month_count = parameters.month_count or 6
        return LLMIntentResponse(
            intent=Intent.GET_USAGE_HISTORY,
            parameters=parameters,
        )

    if any(
        term in text
        for term in ("average", "highest", "most", "lowest", "least")
    ):
        return None

    if (
        any(
            term in text
            for term in (
                "history",
                "each month",
                "every month",
                "graph",
                "graphs",
                "chart",
                "charts",
                "plot",
                "visual",
            )
        )
        or parameters.month_count
    ):
        if usage_type is None:
            return _usage_clarification(text, parameters)
        parameters.usage_type = usage_type
        parameters.month = None
        parameters.comparison_month = None
        return LLMIntentResponse(
            intent=Intent.GET_USAGE_HISTORY,
            parameters=parameters,
        )

    if usage_type == UsageType.DATA:
        return LLMIntentResponse(
            intent=Intent.GET_DATA_USAGE,
            parameters=parameters,
        )

    if usage_type == UsageType.VOICE:
        return LLMIntentResponse(
            intent=Intent.GET_VOICE_USAGE,
            parameters=parameters,
        )

    if usage_type == UsageType.SMS:
        return LLMIntentResponse(
            intent=Intent.GET_SMS_USAGE,
            parameters=parameters,
        )

    if "summary" in text or "all my usage" in text:
        return LLMIntentResponse(
            intent=Intent.GET_USAGE_SUMMARY,
            parameters=parameters,
        )

    return _usage_clarification(text, parameters)


def _classify_unpaid_bills_request(
    text: str,
) -> LLMIntentResponse | None:
    if "bill" not in text and "bills" not in text:
        return None

    if not any(
        phrase in text
        for phrase in (
            "unpaid",
            "not paid",
            "haven't paid",
            "have not paid",
            "overdue bill",
            "overdue bills",
            "past due",
        )
    ):
        return None

    if any(
        phrase in text
        for phrase in (
            "current bill and payment",
            "bill and payment status",
            "has my bill been paid",
            "did i pay",
            "payment status",
        )
    ):
        return None

    parameters = IntentParameters(
        status_filter=BillStatus.UNPAID,
    )
    count = _extract_count(text)
    if count is not None:
        parameters.limit = count

    return LLMIntentResponse(
        intent=Intent.FILTER_BILLS,
        parameters=parameters,
    )


def _classify_simplified_bill_request(
    text: str,
) -> LLMIntentResponse | None:
    if "bill" not in text and "bills" not in text:
        return None

    if any(
        phrase in text
        for phrase in (
            "compare my latest bill",
            "latest bill with the previous",
            "latest bill to the previous",
            "current bill with the previous",
            "this bill with last month",
            "this bill to last month",
            "latest bill with the previous one",
            "latest with the previous one",
            "compare my latest bill with the previous one",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.GET_BILL_COMPARISON,
            parameters=IntentParameters(),
        )

    if _requests_calendar_month_bill_pair(text):
        from datetime import date

        from app.business.dates import shift_month

        today = date.today()
        previous_year, previous_month = shift_month(
            today.year,
            today.month,
            -1,
        )
        return LLMIntentResponse(
            intent=Intent.GET_BILL_COMPARISON,
            parameters=IntentParameters(
                month=today.month,
                year=today.year,
                comparison_month=previous_month,
                comparison_year=previous_year,
            ),
        )

    if any(
        phrase in text
        for phrase in (
            "why did my bill change",
            "bill change from last",
            "bill go up",
            "bill went up",
            "bill go down",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.EXPLAIN_BILL_CHANGE,
            parameters=IntentParameters(),
        )

    if "bill trend" in text or (
        "trend" in text and "bill" in text
    ):
        parameters = IntentParameters()
        count = _extract_count(text)
        parameters.limit = count or 6
        return LLMIntentResponse(
            intent=Intent.GET_BILL_HISTORY,
            parameters=parameters,
        )

    return None


def _classify_billing_service_request(
    text: str,
) -> LLMIntentResponse | None:
    if "bill" not in text and "owe" not in text:
        return None
    if any(
        term in text
        for term in (
            "phone bill",
            "mobile bill",
            "fiber bill",
            "broadband bill",
        )
    ):
        parameters = IntentParameters()
        if "fiber" in text or "broadband" in text:
            parameters.plan_type = PlanType.FIBER
        else:
            parameters.plan_type = PlanType.MOBILE
        return LLMIntentResponse(
            intent=Intent.GET_CURRENT_BILL,
            parameters=parameters,
        )
    return None


def _classify_plan_comparison(
    user_message: str,
    text: str,
) -> LLMIntentResponse | None:
    if "compare" not in text and " versus " not in text and " vs " not in text:
        return None

    plan_ids = [
        match.group(0).upper()
        for match in re.finditer(
            r"\bPLAN[A-Z0-9_-]*\d+[A-Z0-9_-]*\b",
            user_message,
            flags=re.IGNORECASE,
        )
    ]
    if len(plan_ids) < 2:
        return None

    return LLMIntentResponse(
        intent=Intent.GET_PLAN_COMPARISON,
        parameters=IntentParameters(
            plan_id=plan_ids[0],
            comparison_plan_id=plan_ids[1],
        ),
    )


def _classify_subscription_inventory(
    text: str,
) -> LLMIntentResponse | None:
    if any(
        phrase in text
        for phrase in (
            "what services",
            "my services",
            "list subscriptions",
            "how many subscriptions",
            "mobile and fiber",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.GET_LIST_SUBSCRIPTIONS,
        )
    return None


def _classify_explorer_records(
    text: str,
) -> LLMIntentResponse | None:
    parameters = IntentParameters()

    if any(
        phrase in text
        for phrase in (
            "account credit",
            "account credits",
            "do i have any credits",
            "credit balance",
            "available credits",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.GET_ACCOUNT_CREDITS,
            parameters=parameters,
        )

    if any(
        phrase in text
        for phrase in (
            "autopay",
            "auto pay",
            "payment profile",
            "payment method on file",
            "card on file",
            "saved payment method",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.GET_PAYMENT_PROFILE,
            parameters=parameters,
        )

    return None


_NAMED_MONTH_PATTERN = re.compile(
    r"\b("
    r"january|february|march|april|may|june|july|august|"
    r"september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec"
    r")\b",
    flags=re.IGNORECASE,
)


def _message_names_calendar_month(text: str) -> bool:
    for match in _NAMED_MONTH_PATTERN.finditer(text):
        token = match.group(1).lower()
        if token == "may":
            if re.search(
                r"\b(?:in|for|during|of|month of)\s+may\b|"
                r"\bmay\s+(?:data|voice|sms|usage|bill)\b",
                text,
            ):
                return True
            continue
        return True
    return False


def _requests_latest_previous_bill_pair(text: str) -> bool:
    if "bill" not in text:
        return False

    if any(
        phrase in text
        for phrase in (
            "compare my latest bill",
            "latest bill with the previous",
            "latest bill to the previous",
            "latest bill with the previous one",
            "latest with the previous",
            "most recent bill with",
            "current bill with the previous",
            "this bill with last month",
            "this bill to last month",
        )
    ):
        return True

    return (
        "latest" in text
        and "previous" in text
    )


def _requests_calendar_month_bill_pair(text: str) -> bool:
    if "bill" not in text:
        return False

    return (
        "this month" in text
        and "last month" in text
    ) or (
        "current month" in text
        and (
            "previous month" in text
            or "last month" in text
        )
    )


def _align_bill_comparison_with_message(
    user_message: str,
    response: LLMIntentResponse,
) -> LLMIntentResponse:
    if response.intent not in {
        Intent.GET_BILL_COMPARISON,
        Intent.EXPLAIN_BILL_CHANGE,
    }:
        return response

    text = user_message.lower().strip()
    params = response.parameters

    if params.current_bill_id or params.previous_bill_id:
        return response

    if _message_names_calendar_month(text):
        return response

    if _requests_calendar_month_bill_pair(text):
        from datetime import date

        from app.business.dates import shift_month

        today = date.today()
        previous_year, previous_month = shift_month(
            today.year,
            today.month,
            -1,
        )
        params.month = today.month
        params.year = today.year
        params.comparison_month = previous_month
        params.comparison_year = previous_year
        return response

    if _requests_latest_previous_bill_pair(text):
        params.month = None
        params.year = None
        params.comparison_month = None
        params.comparison_year = None

    return response


def _normalize_extracted_intent(
    response: LLMIntentResponse,
    user_message: str | None = None,
) -> LLMIntentResponse:
    from app.intent.retired import (
        is_retired_intent,
        retired_intent_message,
    )

    if is_retired_intent(response.intent):
        return LLMIntentResponse(
            intent=Intent.UNSUPPORTED,
            parameters=IntentParameters(),
            clarification=retired_intent_message(),
        )

    if user_message:
        response = _align_bill_comparison_with_message(
            user_message,
            response,
        )

    return response


def classify_deterministic_request(
    user_message: str,
) -> LLMIntentResponse | None:
    text = (
        user_message
        .lower()
        .strip()
    )

    demo = classify_demo_question(user_message)
    if demo is not None:
        return demo

    # Phase 5 must run before the individual domains.
    unpaid_bills = _classify_unpaid_bills_request(
        text,
    )

    if unpaid_bills is not None:
        return unpaid_bills

    phase5 = classify_phase5_request(
        user_message
    )

    if phase5 is not None:
        return phase5

    payment_help = _classify_general_payment_help(
        text
    )

    if payment_help is not None:
        return payment_help

    billing_service = _classify_billing_service_request(
        text
    )

    if billing_service is not None:
        return billing_service

    simplified_bill = _classify_simplified_bill_request(
        text
    )

    if simplified_bill is not None:
        return simplified_bill

    plan_comparison = _classify_plan_comparison(
        user_message,
        text,
    )

    if plan_comparison is not None:
        return plan_comparison

    subscription_inventory = _classify_subscription_inventory(
        text
    )

    if subscription_inventory is not None:
        return subscription_inventory

    explorer_records = _classify_explorer_records(
        text
    )

    if explorer_records is not None:
        return explorer_records

    # Phase 4 outage limitation.
    if any(
        phrase in text
        for phrase in (
            "outage",
            "network down",
            "network is down",
            "network status in my area",
            "service down in my area",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.UNSUPPORTED,
            clarification=(
                "I don't have structured network or "
                "outage information in the current "
                "NexaTel dataset."
            ),
        )

    support = _classify_support_request(
        user_message,
        text,
    )

    if support is not None:
        return support

    device = _classify_device_request(
        user_message,
        text,
    )

    if device is not None:
        return device

    usage = _classify_usage_request(text)
    if usage is not None:
        return usage

    # All Phase 1-3 requests that are not classified by the
    # deterministic Phase 4/5 shortcuts fall through to the
    # structured LLM prompt. This preserves the existing domain
    # capability without duplicating their deterministic business
    # calculations in this client.
    return None


def classify_prompt_guard_request(
    user_message: str,
) -> LLMIntentResponse:
    return (
        classify_deterministic_request(
            user_message
        )
        or LLMIntentResponse(
            intent=Intent.UNSUPPORTED,
        )
    )


def _parse_intent_response(
    content: str,
) -> LLMIntentResponse:
    payload = json.loads(content)

    if not isinstance(payload, dict):
        raise ValueError("The intent response must be a JSON object.")

    if isinstance(payload.get("intent"), str):
        payload["intent"] = payload["intent"].upper()

    parameters = payload.get("parameters")
    if not isinstance(parameters, dict):
        parameters = {}
        payload["parameters"] = parameters

    parameter_names = (
        "time_range",
        "month",
        "year",
        "comparison_month",
        "comparison_year",
        "month_count",
        "limit",
        "usage_type",
        "percentage_type",
        "extreme_type",
        "current_bill_id",
        "previous_bill_id",
        "bill_extreme_type",
        "status_filter",
        "minimum_amount",
        "sort_order",
        "payment_status",
        "payment_method",
        "transaction_reference",
        "payment_aggregate_type",
        "ticket_id",
        "ticket_status",
        "ticket_priority",
        "ticket_category",
        "unresolved_only",
        "support_sort_order",
        "device_id",
        "device_status",
        "device_type",
        "device_sort_order",
        "device_extreme_type",
    )

    for name in parameter_names:
        if name in payload:
            parameters[name] = payload.pop(name)

    enum_names = (
        "time_range",
        "usage_type",
        "percentage_type",
        "extreme_type",
        "bill_extreme_type",
        "status_filter",
        "sort_order",
        "payment_status",
        "payment_method",
        "payment_aggregate_type",
        "ticket_status",
        "ticket_priority",
        "ticket_category",
        "support_sort_order",
        "device_status",
        "device_type",
        "device_sort_order",
        "device_extreme_type",
    )

    for name in enum_names:
        value = parameters.get(name)
        if isinstance(value, str):
            parameters[name] = value.upper()

    return LLMIntentResponse.model_validate(payload)


# ============================================================
# PROVIDER CLIENT
# ============================================================


class GroqLLMClient:
    """Provider adapter around the Groq OpenAI-compatible API."""

    def __init__(
        self,
        settings: Settings,
    ) -> None:
        if not settings.groq_api_key:
            raise LLMError(
                "GROQ_API_KEY is not configured."
            )

        self._client = OpenAI(
            api_key=settings.groq_api_key,
            base_url=(
                "https://api.groq.com/openai/v1"
            ),
        )

        self._settings = settings
        self._model = settings.groq_model

        self._timeout = (
            settings.llm_timeout_seconds
        )

    def extract_intent(
        self,
        user_message: str,
        *,
        context_hint: str | None = None,
    ) -> LLMIntentResponse:
        deterministic_result = (
            classify_deterministic_request(
                user_message
            )
        )

        if deterministic_result is not None:
            from app.services.response_turn_metrics import (
                log_intent_llm_usage,
            )

            normalized = _normalize_extracted_intent(
                deterministic_result,
                user_message,
            )
            log_intent_llm_usage(
                intent=normalized.intent.value,
                prompt_tokens=None,
                completion_tokens=None,
                total_tokens=None,
                deterministic=True,
            )
            return normalized

        if (
            "prompt-guard"
            in self._model.lower()
        ):
            return (
                classify_prompt_guard_request(
                    user_message
                )
            )

        system_prompt = SYSTEM_PROMPT
        if context_hint:
            system_prompt += (
                "\n\nCURRENT STRUCTURED CONVERSATION CONTEXT\n"
                "Use these trusted references only to resolve clear "
                "follow-up language. Explicit information in the "
                "current user message takes precedence. If the "
                "reference remains ambiguous, ask a concise clarification.\n"
                f"{context_hint}"
            )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        for repair_attempt in range(2):
            response = None
            for attempt in range(3):
                try:
                    response = (
                        self._client
                        .chat
                        .completions
                        .create(
                            messages=messages,
                            model=self._model,
                            temperature=0,
                            max_tokens=768,
                            timeout=self._timeout,
                        )
                    )
                    break

                except RateLimitError as exc:
                    if attempt == 2:
                        raise LLMError(
                            "The language model rate limit was exceeded."
                        ) from exc

                    time.sleep(2 ** attempt)

                except Exception as exc:
                    raise LLMError(
                        "The language model could not process the request."
                    ) from exc

            if response is None:
                raise LLMError(
                    "The language model did not return a response."
                )

            content: str | None = None
            try:
                content = response.choices[0].message.content
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("Empty LLM response.")

                parsed = _parse_intent_response(content)
                from app.services.response_turn_metrics import (
                    extract_usage_tokens,
                    log_intent_llm_usage,
                )

                prompt_t, completion_t, total_t = (
                    extract_usage_tokens(response)
                )
                normalized = _normalize_extracted_intent(
                    parsed,
                    user_message,
                )
                log_intent_llm_usage(
                    intent=normalized.intent.value,
                    prompt_tokens=prompt_t,
                    completion_tokens=completion_t,
                    total_tokens=total_t,
                    deterministic=False,
                )
                return normalized
            except Exception:
                if repair_attempt == 1:
                    break

                messages.extend(
                    [
                        {
                            "role": "assistant",
                            "content": content if isinstance(content, str) else "",
                        },
                        {
                            "role": "user",
                            "content": (
                                "Your previous output did not match the required intent schema. "
                                "Return a corrected JSON object only, with a registered intent, "
                                "a parameters object, and no unsupported fields."
                            ),
                        },
                    ]
                )

        return LLMIntentResponse(
            intent=Intent.UNSUPPORTED,
            clarification=(
                "I couldn't safely interpret that request. Please rephrase it or specify "
                "whether you mean your account, plan, usage, bill, payment, support ticket, "
                "or device."
            ),
        )

    def generate_response(
        self,
        backend_output: str,
        *,
        max_tokens: int | None = None,
        narrative_profile: str = "default",
    ) -> str:
        """Turn a backend-generated factual answer into customer-facing prose."""

        if not backend_output.strip():
            raise LLMError(
                "The backend did not produce an answer to personalize."
            )

        if narrative_profile == "customer_360":
            system_prompt = (
                build_customer_360_response_system_prompt()
            )
            token_cap = max_tokens or (
                self._settings.response_max_tokens_full
            )
        else:
            system_prompt = build_response_system_prompt()
            token_cap = max_tokens or (
                self._settings.response_max_tokens_light
            )

        response = None

        for attempt in range(3):
            try:
                response = (
                    self._client
                    .chat
                    .completions
                    .create(
                        messages=[
                            {
                                "role": "system",
                                "content": system_prompt,
                            },
                            {
                                "role": "user",
                                "content": backend_output,
                            },
                        ],
                        model=self._model,
                        temperature=0.1,
                        max_tokens=token_cap,
                        timeout=self._timeout,
                    )
                )
                break

            except RateLimitError as exc:
                if attempt == 2:
                    raise LLMError(
                        "The language model rate limit was exceeded."
                    ) from exc

                time.sleep(2 ** attempt)

            except Exception as exc:
                raise LLMError(
                    "The language model could not generate a response."
                ) from exc

        if response is None:
            raise LLMError(
                "The language model did not return a response."
            )

        try:
            content = response.choices[0].message.content
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Empty LLM response.")

            from app.services.response_turn_metrics import (
                extract_usage_tokens,
                log_response_rewrite_usage,
            )

            prompt_t, completion_t, total_t = extract_usage_tokens(
                response,
            )
            log_response_rewrite_usage(
                prompt_tokens=prompt_t,
                completion_tokens=completion_t,
                total_tokens=total_t,
                max_tokens=token_cap,
                streamed=False,
            )
            return content.strip()
        except Exception as exc:
            raise LLMError(
                "The language model returned an empty response."
            ) from exc

    def generate_response_stream(
        self,
        backend_output: str,
        *,
        max_tokens: int | None = None,
        narrative_profile: str = "default",
    ) -> Iterator[str]:
        """Yield final-answer text deltas for verified backend output."""

        if not backend_output.strip():
            raise LLMError(
                "The backend did not produce an answer to personalize."
            )

        if narrative_profile == "customer_360":
            system_prompt = (
                build_customer_360_response_system_prompt()
            )
            token_cap = max_tokens or (
                self._settings.response_max_tokens_full
            )
        else:
            system_prompt = build_response_system_prompt()
            token_cap = max_tokens or (
                self._settings.response_max_tokens_light
            )

        stream = None

        for attempt in range(3):
            try:
                stream = (
                    self._client
                    .chat
                    .completions
                    .create(
                        messages=[
                            {
                                "role": "system",
                                "content": system_prompt,
                            },
                            {
                                "role": "user",
                                "content": backend_output,
                            },
                        ],
                        model=self._model,
                        temperature=0.1,
                        max_tokens=token_cap,
                        timeout=self._timeout,
                        stream=True,
                    )
                )
                break

            except RateLimitError as exc:
                if attempt == 2:
                    raise LLMError(
                        "The language model rate limit was exceeded."
                    ) from exc

                time.sleep(2 ** attempt)

            except Exception as exc:
                raise LLMError(
                    "The language model could not generate a response."
                ) from exc

        if stream is None:
            raise LLMError(
                "The language model did not return a response stream."
            )

        try:
            for chunk in stream:
                if not chunk.choices:
                    continue

                content = chunk.choices[0].delta.content
                if isinstance(content, str) and content:
                    yield content

                if getattr(chunk, "usage", None) is not None:
                    from app.services.response_turn_metrics import (
                        extract_usage_tokens,
                        log_response_rewrite_usage,
                    )

                    prompt_t, completion_t, total_t = (
                        extract_usage_tokens(chunk)
                    )
                    log_response_rewrite_usage(
                        prompt_tokens=prompt_t,
                        completion_tokens=completion_t,
                        total_tokens=total_t,
                        max_tokens=token_cap,
                        streamed=True,
                    )
        except Exception as exc:
            raise LLMError(
                "The language model response stream was interrupted."
            ) from exc