"""Additional structured billing handlers."""

from __future__ import annotations

from datetime import date
import sqlite3

from app.business.dates import resolve_usage_period
from app.business.subscription_scope import (
    resolve_usage_plan_row,
)
from app.database.queries.bills import (
    get_latest_bill,
    sum_bill_items_by_type,
)
from app.database.queries.usage import (
    get_usage_totals_by_date_range,
)
from app.models.domain import (
    CustomerContext,
    TimeRange,
)
from app.truth.result import (
    TruthResult,
    database_error_result,
    not_found_result,
    verified_result,
)
from app.truth.sources import source_for_table


def _money(value: float) -> float:
    return round(float(value), 2)


def get_bill_charge_summary(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    bill_item_type: str,
    month_count: int | None = None,
    plan_type: str | None = None,
) -> TruthResult[dict]:
    try:
        summary = sum_bill_items_by_type(
            db,
            customer.customer_id,
            item_type=bill_item_type,
            month_count=month_count,
            plan_type=plan_type,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to summarize those bill charges."
            ),
        )

    if int(summary["bill_count"]) == 0:
        return not_found_result(
            source=source_for_table("bill_items"),
            message=(
                f"No {bill_item_type.lower().replace('_', ' ')} "
                "charges were found for that period."
            ),
        )

    return verified_result(
        {
            "result_type": "BILL_CHARGE_SUMMARY",
            "item_type": bill_item_type,
            "bill_count": int(summary["bill_count"]),
            "total_amount": _money(
                summary["total_amount"]
            ),
            "month_count": month_count,
            "plan_type": plan_type,
        },
        source=source_for_table("bill_items"),
    )


def get_projected_bill(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    plan_type: str | None = None,
) -> TruthResult[dict]:
    plan, error = resolve_usage_plan_row(
        db,
        customer.customer_id,
        plan_type=plan_type,
    )

    if error is not None:
        return error

    assert plan is not None

    try:
        period = resolve_usage_period(
            time_range=TimeRange.CURRENT_MONTH,
            month=None,
            year=None,
        )
        totals = get_usage_totals_by_date_range(
            db,
            customer.customer_id,
            period.start_date.isoformat(),
            period.end_date.isoformat(),
            subscription_id=plan["subscription_id"],
        )
        latest_bill = get_latest_bill(
            db,
            customer.customer_id,
            plan_type=plan["plan_type"],
        )
    except (ValueError, sqlite3.Error):
        return database_error_result(
            message=(
                "Unable to estimate your current bill."
            ),
        )

    base_price = _money(plan["monthly_price"])
    estimated_total = base_price

    data_used = float(totals["data_used_gb"])
    data_limit = float(plan["data_limit_gb"])
    is_unlimited = bool(plan["is_data_unlimited"])

    note = (
        "Estimate uses your plan's monthly price. "
        "Usage overages and one-time charges are not "
        "projected unless they already appear on bills."
    )

    if (
        not is_unlimited
        and data_limit > 0
        and data_used > data_limit
    ):
        note = (
            "Your data usage exceeds the included allowance "
            "this month; the estimate may be higher once "
            "overages are rated."
        )

    return verified_result(
        {
            "result_type": "PROJECTED_BILL",
            "subscription_id": plan["subscription_id"],
            "plan_name": plan["plan_name"],
            "plan_type": plan["plan_type"],
            "estimated_amount": estimated_total,
            "base_plan_amount": base_price,
            "data_used_gb": round(data_used, 2),
            "data_limit_gb": data_limit,
            "is_data_unlimited": is_unlimited,
            "latest_bill_id": (
                latest_bill["bill_id"]
                if latest_bill is not None
                else None
            ),
            "as_of_date": date.today().isoformat(),
            "note": note,
        },
        source=source_for_table("bills"),
    )
