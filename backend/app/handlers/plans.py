"""Handlers for NexaTel plan and subscription intents."""

from __future__ import annotations

import sqlite3

from app.database.queries.plans import get_plan_by_id
from app.database.queries.subscriptions import (
    get_current_subscription,
    get_latest_subscription,
)
from app.models.domain import CustomerContext
from app.truth.result import (
    TruthResult,
    database_error_result,
    not_found_result,
    verified_result,
)
from app.truth.sources import source_for_table


def get_current_plan(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    plan_type: str | None = None,
) -> TruthResult[dict]:
    """Return the customer's currently active plan."""

    try:
        subscription = get_current_subscription(
            db,
            customer_id=customer.customer_id,
            plan_type=plan_type,
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve your current plan.",
        )

    if subscription is None:
        return not_found_result(
            source=source_for_table("subscriptions"),
            message="No active subscription was found.",
        )

    try:
        plan = get_plan_by_id(
            db,
            plan_id=subscription["plan_id"],
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve your plan information.",
        )

    if plan is None:
        return not_found_result(
            source=source_for_table("plans"),
            message=(
                "The plan associated with your subscription "
                "was not found."
            ),
        )

    data = {
        "result_type": "CURRENT_PLAN",
        "subscription_id": subscription["subscription_id"],
        "plan_id": plan["plan_id"],
        "plan_name": plan["name"],
        "plan_type": plan["plan_type"],
        "monthly_price": plan["monthly_price"],
        "data_limit_gb": plan["data_limit_gb"],
        "is_data_unlimited": bool(
            plan["is_data_unlimited"]
        ),
        "voice_limit_minutes": (
            plan["voice_limit_minutes"]
        ),
        "sms_limit": plan["sms_limit"],
        "subscription_status": subscription["status"],
        "start_date": subscription["start_date"],
        "renewal_date": subscription["renewal_date"],
    }

    return verified_result(
        data,
        source=source_for_table("subscriptions"),
    )


def get_plan_renewal(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    plan_type: str | None = None,
) -> TruthResult[dict]:
    """Return the authenticated customer's next plan renewal."""

    try:
        subscription = get_current_subscription(
            db,
            customer_id=customer.customer_id,
            plan_type=plan_type,
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve your renewal information.",
        )

    if subscription is None:
        return not_found_result(
            source=source_for_table("subscriptions"),
            message="No active subscription was found.",
        )

    try:
        plan = get_plan_by_id(
            db,
            plan_id=subscription["plan_id"],
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve your plan information.",
        )

    if plan is None:
        return not_found_result(
            source=source_for_table("plans"),
            message=(
                "The plan associated with your subscription "
                "was not found."
            ),
        )

    data = {
        "result_type": "PLAN_RENEWAL",
        "subscription_id": subscription["subscription_id"],
        "plan_id": subscription["plan_id"],
        "plan_name": plan["name"],
        "plan_type": plan["plan_type"],
        "renewal_date": subscription["renewal_date"],
        "subscription_status": subscription["status"],
    }

    return verified_result(
        data,
        source=source_for_table("subscriptions"),
    )


def get_latest_subscription_overview(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    """Return the latest subscription and its plan, regardless of status."""

    try:
        subscription = get_latest_subscription(
            db,
            customer_id=customer.customer_id,
        )

        if subscription is None:
            return not_found_result(
                source=source_for_table("subscriptions"),
                message="No subscription was found.",
            )

        plan = get_plan_by_id(
            db,
            plan_id=subscription["plan_id"],
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve your subscription information.",
        )

    if plan is None:
        return not_found_result(
            source=source_for_table("plans"),
            message="The plan associated with your subscription was not found.",
        )

    return verified_result(
        {
            "subscription_id": subscription["subscription_id"],
            "subscription_status": subscription["status"],
            "renewal_date": subscription["renewal_date"],
            "plan_name": plan["name"],
            "plan_type": plan["plan_type"],
            "monthly_price": plan["monthly_price"],
            "data_limit_gb": plan["data_limit_gb"],
            "is_data_unlimited": bool(
                plan["is_data_unlimited"]
            ),
        },
        source=source_for_table("subscriptions"),
    )