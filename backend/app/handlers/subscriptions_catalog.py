"""Subscription inventory and plan catalog handlers."""

from __future__ import annotations

import sqlite3

from app.database.queries.plans import (
    get_plan_by_id,
    list_plans,
)
from app.database.queries.subscriptions import (
    list_subscriptions_for_customer,
)
from app.models.domain import CustomerContext
from app.truth.result import (
    TruthResult,
    database_error_result,
    not_found_result,
    validation_error_result,
    verified_result,
)
from app.truth.sources import source_for_table


def _plan_dict(row) -> dict:
    return {
        "plan_id": row["plan_id"],
        "plan_name": row["plan_name"]
        if "plan_name" in row.keys()
        else row["name"],
        "monthly_price": float(row["monthly_price"]),
        "data_limit_gb": float(row["data_limit_gb"]),
        "is_data_unlimited": bool(row["is_data_unlimited"]),
        "voice_limit_minutes": int(row["voice_limit_minutes"]),
        "sms_limit": int(row["sms_limit"]),
        "plan_type": row["plan_type"],
    }


def get_list_subscriptions(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    try:
        rows = list_subscriptions_for_customer(
            db,
            customer.customer_id,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve your subscriptions."
            ),
        )

    if not rows:
        return not_found_result(
            source=source_for_table("subscriptions"),
            message="No subscriptions were found.",
        )

    subscriptions = [
        {
            "subscription_id": row["subscription_id"],
            "status": row["status"],
            "start_date": row["start_date"],
            "renewal_date": row["renewal_date"],
            "plan_id": row["plan_id"],
            "plan_name": row["plan_name"],
            "plan_type": row["plan_type"],
            "monthly_price": float(
                row["monthly_price"]
            ),
        }
        for row in rows
    ]

    return verified_result(
        {
            "result_type": "SUBSCRIPTION_LIST",
            "count": len(subscriptions),
            "subscriptions": subscriptions,
        },
        source=source_for_table("subscriptions"),
    )


def get_plan_catalog(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    plan_type: str | None = None,
) -> TruthResult[dict]:
    del customer

    try:
        rows = list_plans(
            db,
            plan_type=plan_type,
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve the plan catalog.",
        )

    if not rows:
        return not_found_result(
            source=source_for_table("plans"),
            message="No plans matched that request.",
        )

    return verified_result(
        {
            "result_type": "PLAN_CATALOG",
            "count": len(rows),
            "plans": [_plan_dict(row) for row in rows],
        },
        source=source_for_table("plans"),
    )


def get_plan_comparison(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    plan_id: str | None = None,
    comparison_plan_id: str | None = None,
) -> TruthResult[dict]:
    del customer

    if not plan_id or not comparison_plan_id:
        return validation_error_result(
            message=(
                "Please specify two plan IDs to compare."
            ),
        )

    if plan_id == comparison_plan_id:
        return validation_error_result(
            message="Please choose two different plans.",
        )

    try:
        left = get_plan_by_id(db, plan_id)
        right = get_plan_by_id(
            db,
            comparison_plan_id,
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to compare those plans.",
        )

    if left is None or right is None:
        return not_found_result(
            source=source_for_table("plans"),
            message="One or both plans were not found.",
        )

    return verified_result(
        {
            "result_type": "PLAN_COMPARISON",
            "current": _plan_dict(left),
            "previous": _plan_dict(right),
        },
        source=source_for_table("plans"),
    )
