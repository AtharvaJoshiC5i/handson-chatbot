"""Payment profile and account credit handlers."""

from __future__ import annotations

import sqlite3

from app.database.queries.credits import (
    get_available_credit_total,
    list_account_credits,
)
from app.database.queries.payment_profiles import (
    get_payment_profile,
)
from app.models.domain import CustomerContext
from app.truth.result import (
    TruthResult,
    database_error_result,
    not_found_result,
    verified_result,
)
from app.truth.sources import source_for_table


def get_payment_profile_status(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    try:
        profile = get_payment_profile(
            db,
            customer.customer_id,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve your payment profile."
            ),
        )

    if profile is None:
        return not_found_result(
            source=source_for_table(
                "customer_payment_profiles"
            ),
            message=(
                "No saved payment method or autopay setup "
                "is on file for this account."
            ),
        )

    return verified_result(
        {
            "result_type": "PAYMENT_PROFILE",
            "autopay_enabled": bool(
                profile["autopay_enabled"]
            ),
            "default_payment_method": profile[
                "default_payment_method"
            ],
            "payment_method_label": profile[
                "payment_method_label"
            ],
        },
        source=source_for_table(
            "customer_payment_profiles"
        ),
    )


def get_account_credits(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    try:
        credits = list_account_credits(
            db,
            customer.customer_id,
        )
        available_total = get_available_credit_total(
            db,
            customer.customer_id,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve your account credits."
            ),
        )

    if not credits:
        return not_found_result(
            source=source_for_table("account_credits"),
            message="No credits were found on your account.",
        )

    return verified_result(
        {
            "result_type": "ACCOUNT_CREDITS",
            "available_total": round(
                available_total,
                2,
            ),
            "credits": [
                {
                    "credit_id": row["credit_id"],
                    "amount": float(row["amount"]),
                    "reason": row["reason"],
                    "credit_date": row["credit_date"],
                    "status": row["status"],
                }
                for row in credits
            ],
        },
        source=source_for_table("account_credits"),
    )
