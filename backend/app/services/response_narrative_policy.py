"""When to skip or cap Groq response rewriting."""

from __future__ import annotations

from app.config.settings import Settings
from app.models.api import ChatPresentation
from app.models.domain import TruthStatus

# Result types that ship a structured presentation in the UI.
PRESENTATION_RESULT_TYPES = frozenset(
    {
        "USAGE_SUMMARY",
        "USAGE_HISTORY",
        "USAGE_TREND",
        "USAGE_COMPARISON",
        "BILL_HISTORY",
        "BILL_TREND",
        "BILL_BREAKDOWN",
        "BILL_COMPARISON",
        "BILL_FILTER",
        "PLAN_RENEWAL",
        "PLAN_COMPARISON",
        "PAYMENT_HISTORY",
        "PAYMENT_FILTER",
        "SUPPORT_HISTORY",
        "SUPPORT_FILTER",
        "SUPPORT_SUMMARY",
        "DEVICE_LIST",
        "DEVICE_FILTER",
        "DEVICE_SUMMARY",
        "CROSS_PLAN_USAGE_STATUS",
        "CROSS_BILL_PAYMENT_STATUS",
        "CROSS_BILL_PAYMENT_EXPLANATION",
        "CROSS_BILLING_SUPPORT_STATUS",
        "CROSS_PAYMENT_SUPPORT_STATUS",
        "CROSS_ACCOUNT_PLAN_STATUS",
        "CROSS_ACCOUNT_ATTENTION_SUMMARY",
        "CUSTOMER_360",
        "BILL_ANOMALY_DETECTION",
        "PLAN_RECOMMENDATION",
    },
)


def should_skip_response_rewrite(
    status: TruthStatus,
    presentation: ChatPresentation | None,
    mode: str,
    *,
    result_type: str | None = None,
) -> bool:
    if status != TruthStatus.VERIFIED:
        return True

    normalized = mode.strip().lower()

    if normalized == "off":
        return True

    if result_type == "CUSTOMER_360":
        return True

    if result_type in {
        "PAYMENT_LATEST",
        "PAYMENT_PROFILE",
        "PAYMENT_RECONCILIATION",
        "CROSS_BILL_PAYMENT_STATUS",
    }:
        return True

    if presentation is not None and normalized in {
        "auto",
        "light",
    }:
        return True

    return False


def rewrite_max_tokens(
    settings: Settings,
    *,
    has_presentation: bool,
    result_type: str | None = None,
) -> int:
    mode = settings.response_llm_mode.strip().lower()

    if result_type == "CUSTOMER_360":
        return min(
            settings.response_max_tokens_light,
            160,
        )

    if mode == "full":
        return settings.response_max_tokens_full

    if has_presentation:
        return settings.response_max_tokens_light

    return settings.response_max_tokens_light
