"""Handlers for NexaTel payment intents."""

from __future__ import annotations

import sqlite3

from app.database.queries.payments import (
    get_payment_history,
    get_payment_status_for_customer,
)
from app.models.domain import CustomerContext
from app.truth.result import (
    TruthResult,
    database_error_result,
    not_found_result,
    verified_result,
)
from app.truth.sources import source_for_table


def get_payment_status(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    """Return the latest payment status for the authenticated customer."""

    try:
        payment = get_payment_status_for_customer(
            db,
            customer_id=customer.customer_id,
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve your payment status.",
        )

    if payment is None:
        return not_found_result(
            source=source_for_table("payments"),
            message="No payment record was found.",
        )

    return verified_result(
        dict(payment),
        source=source_for_table("payments"),
    )


def get_payment_history_for_customer(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    limit: int = 10,
) -> TruthResult[list[dict]]:
    """Return payment history for the authenticated customer."""

    try:
        payments = get_payment_history(
            db,
            customer_id=customer.customer_id,
            limit=limit,
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve your payment history.",
        )

    if not payments:
        return not_found_result(
            source=source_for_table("payments"),
            message="No payment history was found.",
        )

    return verified_result(
        [dict(payment) for payment in payments],
        source=source_for_table("payments"),
    )