"""Handlers for NexaTel support-ticket intents."""

from __future__ import annotations

import sqlite3

from app.database.queries.support_tickets import (
    get_support_tickets,
)
from app.models.domain import CustomerContext
from app.truth.result import (
    TruthResult,
    database_error_result,
    not_found_result,
    verified_result,
)
from app.truth.sources import source_for_table


def get_customer_support_tickets(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    limit: int = 10,
) -> TruthResult[list[dict]]:
    """Return support tickets belonging to the authenticated customer."""

    try:
        tickets = get_support_tickets(
            db,
            customer_id=customer.customer_id,
            limit=limit,
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve your support tickets.",
        )

    if not tickets:
        return not_found_result(
            source=source_for_table("support_tickets"),
            message="No support tickets were found.",
        )

    return verified_result(
        [dict(ticket) for ticket in tickets],
        source=source_for_table("support_tickets"),
    )