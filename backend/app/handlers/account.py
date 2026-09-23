"""Handlers for NexaTel account-related intents."""

from __future__ import annotations

import sqlite3

from app.database.queries.customers import get_customer
from app.models.domain import CustomerContext
from app.truth.result import (
    TruthResult,
    database_error_result,
    not_found_result,
    verified_result,
)
from app.truth.sources import source_for_table


def get_account_status(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    """Return the authenticated customer's account status.

    Customer identity comes exclusively from CustomerContext.
    """

    try:
        row = get_customer(
            db,
            customer_id=customer.customer_id,
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve account information.",
        )

    if row is None:
        return not_found_result(
            source=source_for_table("customers"),
            message="Customer account was not found.",
        )

    data = {
        "customer_id": row["customer_id"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"],
        "account_status": row["account_status"],
        "created_at": row["created_at"],
    }

    return verified_result(
        data,
        source=source_for_table("customers"),
    )