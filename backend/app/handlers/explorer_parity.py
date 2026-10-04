"""Handlers for explorer-parity list and detail intents."""

from __future__ import annotations

import sqlite3

from app.business.validation import validate_limit
from app.database.queries.bills import list_bill_items_for_customer
from app.database.queries.support_tickets import (
    list_all_ticket_updates_for_customer,
)
from app.database.queries.usage_records import list_usage_records
from app.models.domain import CustomerContext
from app.truth.result import (
    TruthResult,
    database_error_result,
    not_found_result,
    verified_result,
)
from app.truth.sources import source_for_table


def list_usage_records_for_customer(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    subscription_id: str | None = None,
    limit: int | None = None,
) -> TruthResult[dict]:
    row_limit = validate_limit(limit)

    try:
        rows = list_usage_records(
            db,
            customer.customer_id,
            subscription_id=subscription_id,
            limit=row_limit,
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve usage records.",
        )

    if not rows:
        return not_found_result(
            source=source_for_table("usage"),
            message="No usage records matched that request.",
        )

    return verified_result(
        {
            "result_type": "USAGE_RECORD_LIST",
            "count": len(rows),
            "records": [
                {
                    "usage_id": row["usage_id"],
                    "subscription_id": row["subscription_id"],
                    "usage_date": row["usage_date"],
                    "data_used_gb": float(row["data_used_gb"]),
                    "voice_minutes": int(row["voice_minutes"]),
                    "sms_count": int(row["sms_count"]),
                }
                for row in rows
            ],
        },
        source=source_for_table("usage"),
    )


def list_bill_items(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    current_bill_id: str | None = None,
    bill_item_type: str | None = None,
    limit: int | None = None,
) -> TruthResult[dict]:
    row_limit = validate_limit(limit)

    try:
        rows = list_bill_items_for_customer(
            db,
            customer.customer_id,
            bill_id=current_bill_id,
            item_type=bill_item_type,
            limit=row_limit,
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve bill line items.",
        )

    if not rows:
        return not_found_result(
            source=source_for_table("bill_items"),
            message="No bill line items matched that request.",
        )

    return verified_result(
        {
            "result_type": "BILL_ITEM_LIST",
            "count": len(rows),
            "items": [
                {
                    "bill_item_id": row["bill_item_id"],
                    "bill_id": row["bill_id"],
                    "description": row["description"],
                    "amount": float(row["amount"]),
                    "item_type": row["item_type"],
                }
                for row in rows
            ],
        },
        source=source_for_table("bill_items"),
    )


def list_ticket_updates(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    ticket_id: str | None = None,
    limit: int | None = None,
) -> TruthResult[dict]:
    row_limit = validate_limit(limit)

    try:
        rows = list_all_ticket_updates_for_customer(
            db,
            customer.customer_id,
            ticket_id=ticket_id,
            limit=row_limit,
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve ticket updates.",
        )

    if not rows:
        return not_found_result(
            source=source_for_table("support_ticket_updates"),
            message="No ticket updates matched that request.",
        )

    return verified_result(
        {
            "result_type": "TICKET_UPDATE_LIST",
            "count": len(rows),
            "updates": [
                {
                    "update_id": row["update_id"],
                    "ticket_id": row["ticket_id"],
                    "updated_at": row["updated_at"],
                    "status": row["status"],
                    "note": row["note"],
                }
                for row in rows
            ],
        },
        source=source_for_table("support_ticket_updates"),
    )
