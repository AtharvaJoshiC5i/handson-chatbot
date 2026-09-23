"""Handlers for NexaTel billing intents."""

from __future__ import annotations

import sqlite3

from app.business.billing_rules import (
    calculate_bill_difference,
    calculate_bill_item_total,
    calculate_bill_percentage_change,
    calculate_outstanding_amount,
    determine_bill_status,
)
from app.database.queries.bills import (
    get_bill_by_id,
    get_bill_history,
    get_current_bill as query_get_current_bill,
    get_bill_items,
)
from app.models.domain import CustomerContext
from app.truth.result import (
    TruthResult,
    database_error_result,
    not_found_result,
    verified_result,
)
from app.truth.sources import source_for_table


def _bill_to_dict(row: sqlite3.Row) -> dict:
    """Convert a bill database row into a response-safe dictionary."""

    return {
        "bill_id": row["bill_id"],
        "customer_id": row["customer_id"],
        "billing_period_start": row["billing_period_start"],
        "billing_period_end": row["billing_period_end"],
        "due_date": row["due_date"],
        "total_amount": row["total_amount"],
        "paid_amount": row["paid_amount"],
        "status": row["status"],
    }


def get_current_bill(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    """Return the authenticated customer's current bill."""

    try:
        bill = query_get_current_bill(
            db,
            customer_id=customer.customer_id,
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve your current bill.",
        )

    if bill is None:
        return not_found_result(
            source=source_for_table("bills"),
            message="No current bill was found.",
        )

    try:
        items = get_bill_items(
            db,
            bill_id=bill["bill_id"],
            customer_id=customer.customer_id,
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve your bill details.",
        )

    calculated_total = calculate_bill_item_total(
        item["amount"]
        for item in items
    )

    outstanding = calculate_outstanding_amount(
        bill["total_amount"],
        bill["paid_amount"],
    )

    data = _bill_to_dict(bill)

    data.update(
        {
            "items": [dict(item) for item in items],
            "calculated_item_total": float(calculated_total),
            "outstanding_amount": float(outstanding),
            "derived_status": determine_bill_status(
                bill["total_amount"],
                bill["paid_amount"],
                bill["status"],
            ).value,
        }
    )

    return verified_result(
        data,
        source=source_for_table("bills"),
    )


def get_bill_history_for_customer(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    limit: int = 10,
) -> TruthResult[list[dict]]:
    """Return bill history for the authenticated customer."""

    try:
        bills = get_bill_history(
            db,
            customer_id=customer.customer_id,
            limit=limit,
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve your bill history.",
        )

    if not bills:
        return not_found_result(
            source=source_for_table("bills"),
            message="No bill history was found.",
        )

    return verified_result(
        [_bill_to_dict(bill) for bill in bills],
        source=source_for_table("bills"),
    )


def get_total_spending(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    limit: int = 20,
) -> TruthResult[dict]:
    """Calculate total spending from verified bill records."""

    try:
        bills = get_bill_history(
            db,
            customer_id=customer.customer_id,
            limit=limit,
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve your spending history.",
        )

    if not bills:
        return not_found_result(
            source=source_for_table("bills"),
            message="No billing records were found.",
        )

    total = sum(
        float(bill["total_amount"])
        for bill in bills
    )

    return verified_result(
        {
            "customer_id": customer.customer_id,
            "bill_count": len(bills),
            "total_spending": total,
            "bills": [
                _bill_to_dict(bill)
                for bill in bills
            ],
        },
        source=source_for_table("bills"),
    )


def get_bill_comparison(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    current_bill_id: str | None = None,
    previous_bill_id: str | None = None,
) -> TruthResult[dict]:
    """
    Compare two customer-owned bills.

    If no IDs are supplied, the two most recent customer bills are
    compared automatically.

    If IDs are supplied, both must be supplied.
    """

    if (current_bill_id is None) != (
        previous_bill_id is None
    ):
        return not_found_result(
            source=source_for_table("bills"),
            message=(
                "Please provide both bill IDs when comparing "
                "specific bills."
            ),
        )

    try:
        if (
            current_bill_id is None
            and previous_bill_id is None
        ):
            bills = get_bill_history(
                db,
                customer_id=customer.customer_id,
                limit=2,
            )

            if len(bills) < 2:
                return not_found_result(
                    source=source_for_table("bills"),
                    message=(
                        "At least two bills are required "
                        "for comparison."
                    ),
                )

            current_bill = bills[0]
            previous_bill = bills[1]

        else:
            current_bill = get_bill_by_id(
                db,
                bill_id=current_bill_id,
                customer_id=customer.customer_id,
            )

            previous_bill = get_bill_by_id(
                db,
                bill_id=previous_bill_id,
                customer_id=customer.customer_id,
            )

    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve bills for comparison.",
        )

    if (
        current_bill is None
        or previous_bill is None
    ):
        return not_found_result(
            source=source_for_table("bills"),
            message="One or both bills could not be found.",
        )

    current_total = current_bill["total_amount"]
    previous_total = previous_bill["total_amount"]

    difference = calculate_bill_difference(
        previous_total,
        current_total,
    )

    percentage_change = calculate_bill_percentage_change(
        previous_total,
        current_total,
    )

    data = {
        "current_bill": _bill_to_dict(current_bill),
        "previous_bill": _bill_to_dict(previous_bill),
        "difference": float(difference),
        "percentage_change": (
            float(percentage_change)
            if percentage_change is not None
            else None
        ),
    }

    return verified_result(
        data,
        source=source_for_table("bills"),
    )