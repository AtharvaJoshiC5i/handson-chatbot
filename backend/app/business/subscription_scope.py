"""Resolve subscription scope for multi-service customers."""

from __future__ import annotations

import sqlite3

from app.database.queries.subscriptions import (
    count_active_plan_types,
    get_usage_plan_for_customer,
)
from app.truth.result import (
    TruthResult,
    ambiguous_result,
    not_found_result,
)
from app.truth.sources import source_for_table


def plan_type_disambiguation_message() -> str:
    return (
        "You have more than one active NexaTel service. "
        "Do you want mobile or fiber details?"
    )


def resolve_usage_plan_row(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    plan_type: str | None,
) -> tuple[sqlite3.Row | None, TruthResult | None]:
    """Return a subscription/plan row for usage calculations."""

    try:
        plan = get_usage_plan_for_customer(
            db,
            customer_id,
            plan_type=plan_type,
        )
    except sqlite3.Error:
        return (
            None,
            not_found_result(
                source=source_for_table(
                    "subscriptions"
                ),
                message=(
                    "Unable to retrieve subscription "
                    "information."
                ),
            ),
        )

    if plan is None:
        return (
            None,
            not_found_result(
                source=source_for_table(
                    "subscriptions"
                ),
                message=(
                    "No subscription information "
                    "was found for your account."
                ),
            ),
        )

    return plan, None


def resolve_billing_plan_type(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    plan_type: str | None,
) -> TruthResult | None:
    """Return AMBIGUOUS when billing needs an explicit service line."""

    if plan_type is not None:
        return None

    if count_active_plan_types(
        db,
        customer_id,
    ) > 1:
        return ambiguous_result(
            message=plan_type_disambiguation_message(),
            source=source_for_table(
                "subscriptions"
            ),
        )

    return None
