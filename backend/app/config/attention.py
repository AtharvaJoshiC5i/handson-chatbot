"""Deterministic Phase 5 account-attention rules."""

from __future__ import annotations


HIGH_USAGE_ATTENTION_PERCENTAGE = 85.0

PLAN_RENEWAL_ALERT_DAYS = 7


ATTENTION_BILL_STATUSES = frozenset(
    {
        "UNPAID",
        "OVERDUE",
        "PARTIALLY_PAID",
    }
)


ATTENTION_PAYMENT_STATUSES = frozenset(
    {
        "FAILED",
        "PENDING",
    }
)


ATTENTION_SUPPORT_STATUSES = frozenset(
    {
        "OPEN",
        "IN_PROGRESS",
    }
)


ATTENTION_SUPPORT_PRIORITIES = frozenset(
    {
        "HIGH",
        "CRITICAL",
    }
)


ATTENTION_ACCOUNT_STATUSES = frozenset(
    {
        "SUSPENDED",
    }
)


ATTENTION_SUBSCRIPTION_STATUSES = frozenset(
    {
        "SUSPENDED",
    }
)