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
        "result_type": "ACCOUNT_STATUS",
        "customer_id": row["customer_id"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"],
        "city": row["city"],
        "service_address_line": row["service_address_line"],
        "service_state": row["service_state"],
        "service_postal_code": row["service_postal_code"],
        "account_status": row["account_status"],
        "registration_date": row["created_at"],
    }

    return verified_result(
        data,
        source=source_for_table("customers"),
    )