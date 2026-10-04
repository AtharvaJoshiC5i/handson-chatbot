"""Deterministic billing and spending intelligence handlers."""

from __future__ import annotations

from calendar import month_name
from datetime import date
import sqlite3
from statistics import mean

from app.business.subscription_scope import (
    resolve_billing_plan_type,
)
from app.database.queries.bills import (
    get_bill_by_id_for_customer,
    get_bill_for_month,
    get_bill_history,
    get_bill_item_total,
    get_bill_items,
    get_bills_for_date_range,
    get_filtered_bills,
    get_latest_bill,
    get_previous_bill,
)
from app.models.domain import (
    BillExtremeType,
    BillSortOrder,
    BillStatus,
    CustomerContext,
    TimeRange,
)
from app.truth.result import (
    TruthResult,
    database_error_result,
    not_found_result,
    validation_error_result,
    verified_result,
)
from app.truth.sources import source_for_table


def _money(
    value: float,
) -> float:
    return round(
        float(value),
        2,
    )


def _bill_period_label(
    bill,
) -> str:
    value = date.fromisoformat(
        bill["billing_period_start"]
    )

    return (
        f"{month_name[value.month]} "
        f"{value.year}"
    )


def _bill_dict(
    bill,
) -> dict:
    return {
        "bill_id": bill["bill_id"],
        "billing_period_start": (
            bill["billing_period_start"]
        ),
        "billing_period_end": (
            bill["billing_period_end"]
        ),
        "period": _bill_period_label(
            bill
        ),
        "amount": _money(
            bill["amount"]
        ),
        "amount_value": float(
            bill["amount"]
        ),
        "due_date": bill[
            "due_date"
        ],
        "status": bill[
            "status"
        ],
        "subscription_id": bill[
            "subscription_id"
        ],
        "plan_type": bill[
            "plan_type"
        ],
    }


def _resolve_bill(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    bill_id: str | None = None,
    month: int | None = None,
    year: int | None = None,
    plan_type: str | None = None,
):
    if bill_id is not None:
        return get_bill_by_id_for_customer(
            db,
            customer.customer_id,
            bill_id,
        )

    if month is not None:
        resolved_year = (
            year
            if year is not None
            else date.today().year
        )

        return get_bill_for_month(
            db,
            customer.customer_id,
            resolved_year,
            month,
            plan_type=plan_type,
        )

    return get_latest_bill(
        db,
        customer.customer_id,
        plan_type=plan_type,
    )


def _validated_items(
    db: sqlite3.Connection,
    bill,
) -> tuple[
    list[sqlite3.Row] | None,
    str | None,
]:
    items = get_bill_items(
        db,
        bill["bill_id"],
    )

    total = get_bill_item_total(
        db,
        bill["bill_id"],
    )

    if total["item_count"] == 0:
        return (
            [],
            None,
        )

    if abs(
        float(total["item_total"])
        - float(bill["amount"])
    ) > 0.01:
        return (
            None,
            (
                "The stored bill items do not match "
                "the bill total, so I can't provide "
                "a verified breakdown for this bill."
            ),
        )

    return (
        items,
        None,
    )


def get_current_bill(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    plan_type: str | None = None,
) -> TruthResult[dict]:
    ambiguity = resolve_billing_plan_type(
        db,
        customer.customer_id,
        plan_type=plan_type,
    )
    if ambiguity is not None:
        return ambiguity

    try:
        bill = get_latest_bill(
            db,
            customer.customer_id,
            plan_type=plan_type,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve your current bill."
            ),
        )

    if bill is None:
        return not_found_result(
            source=source_for_table(
                "bills"
            ),
            message=(
                "I don't have a bill record "
                "for your account."
            ),
        )

    return verified_result(
        {
            "result_type": "BILL_CURRENT",
            **_bill_dict(bill),
        },
        source=source_for_table(
            "bills"
        ),
    )


def get_specific_bill(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    month: int | None = None,
    year: int | None = None,
    time_range: TimeRange | None = None,
    plan_type: str | None = None,
) -> TruthResult[dict]:
    if (
        month is None
        and time_range
        != TimeRange.LAST_MONTH
    ):
        return validation_error_result(
            message=(
                "A billing month is required."
            ),
        )

    today = date.today()

    if (
        time_range
        == TimeRange.LAST_MONTH
        and month is None
    ):
        if today.month == 1:
            month = 12
            year = today.year - 1
        else:
            month = today.month - 1
            year = today.year

    resolved_year = (
        year
        if year is not None
        else today.year
    )

    try:
        bill = get_bill_for_month(
            db,
            customer.customer_id,
            resolved_year,
            month,
            plan_type=plan_type,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve that bill."
            ),
        )

    if bill is None:
        return not_found_result(
            source=source_for_table(
                "bills"
            ),
            message=(
                "I don't have a bill record for "
                f"{month_name[month]} "
                f"{resolved_year}."
            ),
        )

    return verified_result(
        {
            "result_type": "BILL_SPECIFIC",
            **_bill_dict(bill),
        },
        source=source_for_table(
            "bills"
        ),
    )


def get_bill_history_for_customer(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    limit: int | None = None,
    plan_type: str | None = None,
) -> TruthResult[dict]:
    try:
        bills = get_bill_history(
            db,
            customer.customer_id,
            limit=(
                limit
                if limit is not None
                else 6
            ),
            plan_type=plan_type,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve your billing history."
            ),
        )

    if not bills:
        return not_found_result(
            source=source_for_table(
                "bills"
            ),
            message=(
                "I don't have billing history "
                "for your account."
            ),
        )

    return verified_result(
        {
            "result_type": "BILL_HISTORY",
            "bills": [
                _bill_dict(
                    bill
                )
                for bill in bills
            ],
        },
        source=source_for_table(
            "bills"
        ),
    )


def get_bill_breakdown(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    month: int | None = None,
    year: int | None = None,
    current_bill_id: str | None = None,
) -> TruthResult[dict]:
    try:
        bill = _resolve_bill(
            db,
            customer,
            bill_id=current_bill_id,
            month=month,
            year=year,
        )

        if bill is None:
            return not_found_result(
                source=source_for_table(
                    "bills"
                ),
                message=(
                    "I don't have a bill record "
                    "for that period."
                ),
            )

        items, error = _validated_items(
            db,
            bill,
        )

    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve the bill breakdown."
            ),
        )

    if error is not None:
        return validation_error_result(
            message=error,
        )

    if not items:
        return not_found_result(
            source=source_for_table(
                "bill_items"
            ),
            message=(
                "I can confirm the bill total, "
                "but item-level details are not "
                "available for this bill."
            ),
        )

    return verified_result(
        {
            "result_type": "BILL_BREAKDOWN",
            "bill": _bill_dict(
                bill
            ),
            "items": [
                {
                    "bill_item_id": item[
                        "bill_item_id"
                    ],
                    "description": item[
                        "description"
                    ],
                    "item_type": item[
                        "item_type"
                    ],
                    "amount": _money(
                        item["amount"]
                    ),
                }
                for item in items
            ],
            "validated_total": _money(
                sum(
                    float(item["amount"])
                    for item in items
                )
            ),
        },
        source=source_for_table(
            "bill_items"
        ),
    )


def _comparison_bills(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    current_bill_id: str | None = None,
    previous_bill_id: str | None = None,
    month: int | None = None,
    year: int | None = None,
    comparison_month: int | None = None,
    comparison_year: int | None = None,
):
    current = _resolve_bill(
        db,
        customer,
        bill_id=current_bill_id,
        month=month,
        year=year,
    )

    if current is None:
        return (
            None,
            None,
        )

    if previous_bill_id is not None:
        previous = (
            get_bill_by_id_for_customer(
                db,
                customer.customer_id,
                previous_bill_id,
            )
        )

    elif comparison_month is not None:
        previous = get_bill_for_month(
            db,
            customer.customer_id,
            (
                comparison_year
                if comparison_year is not None
                else (
                    year
                    if year is not None
                    else date.today().year
                )
            ),
            comparison_month,
        )

    else:
        previous = get_previous_bill(
            db,
            customer.customer_id,
            current[
                "billing_period_start"
            ],
        )

    return (
        current,
        previous,
    )


def get_bill_comparison(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    current_bill_id: str | None = None,
    previous_bill_id: str | None = None,
    month: int | None = None,
    year: int | None = None,
    comparison_month: int | None = None,
    comparison_year: int | None = None,
) -> TruthResult[dict]:
    try:
        current, previous = (
            _comparison_bills(
                db,
                customer,
                current_bill_id=(
                    current_bill_id
                ),
                previous_bill_id=(
                    previous_bill_id
                ),
                month=month,
                year=year,
                comparison_month=(
                    comparison_month
                ),
                comparison_year=(
                    comparison_year
                ),
            )
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to compare your bills."
            ),
        )

    if current is None:
        return not_found_result(
            source=source_for_table(
                "bills"
            ),
            message=(
                "I don't have the requested "
                "current bill."
            ),
        )

    if previous is None:
        return not_found_result(
            source=source_for_table(
                "bills"
            ),
            message=(
                "I can see the requested bill, "
                "but I don't have a previous bill "
                "available to compare it with."
            ),
        )

    difference = (
        float(current["amount"])
        - float(previous["amount"])
    )

    if difference > 0:
        direction = "INCREASE"

    elif difference < 0:
        direction = "DECREASE"

    else:
        direction = "NO_CHANGE"

    percentage_change = None

    if float(
        previous["amount"]
    ) != 0:
        percentage_change = round(
            (
                difference
                / float(previous["amount"])
            )
            * 100,
            1,
        )

    return verified_result(
        {
            "result_type": "BILL_COMPARISON",
            "current_bill": _bill_dict(
                current
            ),
            "comparison_bill": _bill_dict(
                previous
            ),
            "signed_difference": _money(
                difference
            ),
            "absolute_difference": _money(
                abs(difference)
            ),
            "percentage_change": (
                percentage_change
            ),
            "direction": direction,
        },
        source=source_for_table(
            "bills"
        ),
    )


def _group_items(
    items: list[sqlite3.Row],
) -> dict[str, dict]:
    grouped: dict[str, dict] = {}

    for item in items:
        item_type = item[
            "item_type"
        ]

        if item_type not in grouped:
            grouped[item_type] = {
                "item_type": item_type,
                "descriptions": [],
                "amount": 0.0,
            }

        grouped[item_type][
            "descriptions"
        ].append(
            item["description"]
        )

        grouped[item_type][
            "amount"
        ] += float(
            item["amount"]
        )

    for value in grouped.values():
        value["amount"] = _money(
            value["amount"]
        )

    return grouped


def explain_bill_change(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    current_bill_id: str | None = None,
    previous_bill_id: str | None = None,
    month: int | None = None,
    year: int | None = None,
    comparison_month: int | None = None,
    comparison_year: int | None = None,
) -> TruthResult[dict]:
    try:
        current, previous = (
            _comparison_bills(
                db,
                customer,
                current_bill_id=(
                    current_bill_id
                ),
                previous_bill_id=(
                    previous_bill_id
                ),
                month=month,
                year=year,
                comparison_month=(
                    comparison_month
                ),
                comparison_year=(
                    comparison_year
                ),
            )
        )

        if current is None:
            return not_found_result(
                source=source_for_table(
                    "bills"
                ),
                message=(
                    "I don't have the requested bill."
                ),
            )

        if previous is None:
            return not_found_result(
                source=source_for_table(
                    "bills"
                ),
                message=(
                    "I can see your current bill, "
                    "but I don't have a previous bill "
                    "available to compare it with."
                ),
            )

        current_items, current_error = (
            _validated_items(
                db,
                current,
            )
        )

        previous_items, previous_error = (
            _validated_items(
                db,
                previous,
            )
        )

    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to explain the bill change."
            ),
        )

    total_difference = (
        float(current["amount"])
        - float(previous["amount"])
    )

    if (
        current_error is not None
        or previous_error is not None
    ):
        return validation_error_result(
            message=(
                "I can confirm the bill changed by "
                f"₹{abs(_money(total_difference))}, "
                "but the available item-level data "
                "is inconsistent, so I can't provide "
                "a verified explanation."
            ),
        )

    if (
        not current_items
        or not previous_items
    ):
        return verified_result(
            {
                "result_type": (
                    "BILL_CHANGE_INSUFFICIENT_DETAIL"
                ),
                "current_bill": _bill_dict(
                    current
                ),
                "comparison_bill": _bill_dict(
                    previous
                ),
                "total_difference": _money(
                    total_difference
                ),
                "added_items": [],
                "removed_items": [],
                "changed_items": [],
                "unchanged_items": [],
            },
            source=source_for_table(
                "bills"
            ),
        )

    current_grouped = _group_items(
        current_items
    )

    previous_grouped = _group_items(
        previous_items
    )

    all_types = (
        set(current_grouped)
        | set(previous_grouped)
    )

    added_items = []
    removed_items = []
    changed_items = []
    unchanged_items = []

    for item_type in sorted(
        all_types
    ):
        current_item = (
            current_grouped.get(
                item_type
            )
        )

        previous_item = (
            previous_grouped.get(
                item_type
            )
        )

        if (
            current_item is not None
            and previous_item is None
        ):
            added_items.append(
                current_item
            )

            continue

        if (
            current_item is None
            and previous_item is not None
        ):
            removed_items.append(
                previous_item
            )

            continue

        current_amount = float(
            current_item["amount"]
        )

        previous_amount = float(
            previous_item["amount"]
        )

        difference = (
            current_amount
            - previous_amount
        )

        item = {
            "item_type": item_type,
            "current_descriptions": (
                current_item[
                    "descriptions"
                ]
            ),
            "previous_descriptions": (
                previous_item[
                    "descriptions"
                ]
            ),
            "current_amount": _money(
                current_amount
            ),
            "previous_amount": _money(
                previous_amount
            ),
            "difference": _money(
                difference
            ),
        }

        if abs(
            difference
        ) <= 0.01:
            unchanged_items.append(
                item
            )
        else:
            changed_items.append(
                item
            )

    if total_difference > 0:
        direction = "INCREASE"

    elif total_difference < 0:
        direction = "DECREASE"

    else:
        direction = "NO_CHANGE"

    return verified_result(
        {
            "result_type": "BILL_CHANGE_EXPLANATION",
            "current_bill": _bill_dict(
                current
            ),
            "comparison_bill": _bill_dict(
                previous
            ),
            "total_difference": _money(
                total_difference
            ),
            "direction": direction,
            "added_items": added_items,
            "removed_items": removed_items,
            "changed_items": changed_items,
            "unchanged_items": unchanged_items,
        },
        source=source_for_table(
            "bill_items"
        ),
    )


def get_total_spending(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    limit: int | None = None,
    month_count: int | None = None,
    time_range: TimeRange | None = None,
) -> TruthResult[dict]:
    try:
        bills = get_bill_history(
            db,
            customer.customer_id,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to calculate your total billed amount."
            ),
        )

    if not bills:
        return not_found_result(
            source=source_for_table(
                "bills"
            ),
            message=(
                "I don't have billing history "
                "for your account."
            ),
        )

    selected = list(
        bills
    )

    if time_range == TimeRange.CURRENT_YEAR:
        current_year = (
            date.today().year
        )

        selected = [
            bill
            for bill in selected
            if int(
                bill[
                    "billing_period_start"
                ][:4]
            )
            == current_year
        ]

    requested_count = (
        month_count
        if month_count is not None
        else limit
    )

    if requested_count is not None:
        selected = selected[
            :requested_count
        ]

    if not selected:
        return not_found_result(
            source=source_for_table(
                "bills"
            ),
            message=(
                "I don't have bills for "
                "the requested period."
            ),
        )

    total = sum(
        float(bill["amount"])
        for bill in selected
    )

    return verified_result(
        {
            "result_type": "BILL_TOTAL_SPENDING",
            "bill_count": len(
                selected
            ),
            "total_billed_amount": _money(
                total
            ),
            "bills": [
                _bill_dict(
                    bill
                )
                for bill in selected
            ],
        },
        source=source_for_table(
            "bills"
        ),
    )


def get_average_bill(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    month_count: int | None = None,
) -> TruthResult[dict]:
    try:
        bills = get_bill_history(
            db,
            customer.customer_id,
            limit=(
                month_count
                if month_count is not None
                else 6
            ),
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to calculate your average bill."
            ),
        )

    if not bills:
        return not_found_result(
            source=source_for_table(
                "bills"
            ),
            message=(
                "I don't have billing history "
                "for your account."
            ),
        )

    average = mean(
        float(bill["amount"])
        for bill in bills
    )

    return verified_result(
        {
            "result_type": "BILL_AVERAGE",
            "bill_count": len(
                bills
            ),
            "average_amount": _money(
                average
            ),
            "bills": [
                _bill_dict(
                    bill
                )
                for bill in bills
            ],
        },
        source=source_for_table(
            "bills"
        ),
    )


def get_bill_extreme(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    bill_extreme_type: BillExtremeType,
    month_count: int | None = None,
) -> TruthResult[dict]:
    try:
        bills = get_bill_history(
            db,
            customer.customer_id,
            limit=month_count,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to analyze your billing history."
            ),
        )

    if not bills:
        return not_found_result(
            source=source_for_table(
                "bills"
            ),
            message=(
                "I don't have billing history "
                "for your account."
            ),
        )

    if (
        bill_extreme_type
        == BillExtremeType.HIGHEST
    ):
        selected = max(
            bills,
            key=lambda bill: float(
                bill["amount"]
            ),
        )
    else:
        selected = min(
            bills,
            key=lambda bill: float(
                bill["amount"]
            ),
        )

    return verified_result(
        {
            "result_type": "BILL_EXTREME",
            "extreme_type": (
                bill_extreme_type.value
            ),
            "bill": _bill_dict(
                selected
            ),
            "history_count": len(
                bills
            ),
        },
        source=source_for_table(
            "bills"
        ),
    )


def get_bill_trend(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    month_count: int | None = None,
) -> TruthResult[dict]:
    try:
        bills = get_bill_history(
            db,
            customer.customer_id,
            limit=(
                month_count
                if month_count is not None
                else 6
            ),
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to analyze your billing trend."
            ),
        )

    if len(bills) < 2:
        return not_found_result(
            source=source_for_table(
                "bills"
            ),
            message=(
                "I need at least two bills to "
                "describe a billing trend."
            ),
        )

    chronological = list(
        reversed(
            bills
        )
    )

    values = [
        float(bill["amount"])
        for bill in chronological
    ]

    increases = sum(
        1
        for previous, current
        in zip(
            values,
            values[1:],
        )
        if current > previous
    )

    decreases = sum(
        1
        for previous, current
        in zip(
            values,
            values[1:],
        )
        if current < previous
    )

    if increases > decreases:
        trend = "GENERALLY_INCREASING"

    elif decreases > increases:
        trend = "GENERALLY_DECREASING"

    else:
        if values[-1] > values[0]:
            trend = "GENERALLY_INCREASING"

        elif values[-1] < values[0]:
            trend = "GENERALLY_DECREASING"

        else:
            trend = "STABLE"

    return verified_result(
        {
            "result_type": "BILL_TREND",
            "trend": trend,
            "bill_count": len(
                chronological
            ),
            "first_bill": _bill_dict(
                chronological[0]
            ),
            "last_bill": _bill_dict(
                chronological[-1]
            ),
            "bills": [
                _bill_dict(
                    bill
                )
                for bill in chronological
            ],
        },
        source=source_for_table(
            "bills"
        ),
    )


def filter_bills(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    status_filter: BillStatus | None = None,
    minimum_amount: float | None = None,
    sort_order: BillSortOrder | None = None,
    limit: int | None = None,
    plan_type: str | None = None,
) -> TruthResult[dict]:
    try:
        bills = get_filtered_bills(
            db,
            customer.customer_id,
            status=(
                status_filter.value
                if status_filter
                is not None
                else None
            ),
            minimum_amount=(
                minimum_amount
            ),
            limit=limit,
            plan_type=plan_type,
            sort_order=(
                sort_order.value
                if sort_order
                is not None
                else "NEWEST"
            ),
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to filter your bills."
            ),
        )

    if not bills:
        return not_found_result(
            source=source_for_table(
                "bills"
            ),
            message=(
                "I don't have any bills matching "
                "those criteria."
            ),
        )

    return verified_result(
        {
            "result_type": "BILL_FILTER",
            "status_filter": (
                status_filter.value
                if status_filter
                is not None
                else None
            ),
            "minimum_amount": (
                minimum_amount
            ),
            "sort_order": (
                sort_order.value
                if sort_order
                is not None
                else "NEWEST"
            ),
            "bills": [
                _bill_dict(
                    bill
                )
                for bill in bills
            ],
        },
        source=source_for_table(
            "bills"
        ),
    )