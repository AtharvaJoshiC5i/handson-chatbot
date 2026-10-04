"""Deterministic handlers for NexaTel usage intelligence."""

from __future__ import annotations

from calendar import month_name
from datetime import date
import sqlite3
from statistics import mean

from app.business.dates import (
    DateRange,
    month_date_range,
    resolve_usage_period,
    shift_month,
)
from app.business.subscription_scope import (
    resolve_usage_plan_row,
)
from app.database.queries.usage import (
    get_monthly_usage_totals,
    get_usage_totals_by_date_range,
)
from app.models.domain import (
    CustomerContext,
    TimeRange,
    UsageExtremeType,
    UsagePercentageType,
    UsageType,
)
from app.truth.result import (
    TruthResult,
    database_error_result,
    not_found_result,
    validation_error_result,
    verified_result,
)
from app.truth.sources import source_for_table


USAGE_CONFIG = {
    UsageType.DATA: {
        "field": "data_used_gb",
        "allowance_field": "data_limit_gb",
        "unit": "GB",
    },
    UsageType.VOICE: {
        "field": "voice_minutes",
        "allowance_field": "voice_limit_minutes",
        "unit": "minutes",
    },
    UsageType.SMS: {
        "field": "sms_count",
        "allowance_field": "sms_limit",
        "unit": "SMS",
    },
}


def _period_label(
    value: DateRange,
) -> str:
    return (
        f"{month_name[value.start_date.month]} "
        f"{value.start_date.year}"
    )


def _period_from_key(
    key: str,
) -> str:
    year_text, month_text = key.split(
        "-",
        1,
    )

    return (
        f"{month_name[int(month_text)]} "
        f"{year_text}"
    )


def _round_value(
    value: float,
    usage_type: UsageType,
) -> float | int:
    if usage_type == UsageType.DATA:
        return round(
            float(value),
            2,
        )

    return int(
        round(float(value))
    )


def _resolve_period(
    *,
    time_range: TimeRange | None,
    month: int | None,
    year: int | None,
) -> tuple[
    DateRange | None,
    TruthResult[None] | None,
]:
    try:
        return (
            resolve_usage_period(
                time_range=time_range,
                month=month,
                year=year,
            ),
            None,
        )
    except ValueError as exc:
        return (
            None,
            validation_error_result(
                message=str(exc),
            ),
        )




def _get_plan(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    plan_type: str | None = None,
):
    plan, error = resolve_usage_plan_row(
        db,
        customer.customer_id,
        plan_type=plan_type,
    )
    if error is not None:
        return None, error
    return plan, None


def _get_period_totals(
    db: sqlite3.Connection,
    customer: CustomerContext,
    period: DateRange,
    *,
    subscription_id: str | None,
):
    return get_usage_totals_by_date_range(
        db,
        customer.customer_id,
        period.start_date.isoformat(),
        period.end_date.isoformat(),
        subscription_id=subscription_id,
    )


def _metric_value(
    row,
    usage_type: UsageType,
) -> float:
    config = USAGE_CONFIG[
        usage_type
    ]

    return float(
        row[config["field"]]
    )


def _allowance_value(
    plan,
    usage_type: UsageType,
) -> float:
    config = USAGE_CONFIG[
        usage_type
    ]

    return float(
        plan[
            config["allowance_field"]
        ]
    )


def _is_unlimited(
    plan,
    usage_type: UsageType,
) -> bool:
    return (
        usage_type == UsageType.DATA
        and bool(
            plan["is_data_unlimited"]
        )
    )


def _is_applicable(
    plan,
    usage_type: UsageType,
) -> bool:
    if (
        plan["plan_type"] == "FIBER"
        and usage_type
        in {
            UsageType.VOICE,
            UsageType.SMS,
        }
    ):
        return False

    return True


def _build_metric(
    *,
    plan,
    totals,
    usage_type: UsageType,
) -> dict:
    config = USAGE_CONFIG[
        usage_type
    ]

    used = _round_value(
        _metric_value(
            totals,
            usage_type,
        ),
        usage_type,
    )

    unlimited = _is_unlimited(
        plan,
        usage_type,
    )

    allowance = _allowance_value(
        plan,
        usage_type,
    )

    result = {
        "usage_type": usage_type.value,
        "used": used,
        "unit": config["unit"],
        "is_unlimited": unlimited,
    }

    if unlimited:
        result.update(
            {
                "allowance": None,
                "remaining": None,
                "over_allowance": 0,
                "consumed_percentage": None,
                "remaining_percentage": None,
            }
        )

        return result

    remaining_raw = (
        allowance
        - float(used)
    )

    remaining = max(
        remaining_raw,
        0,
    )

    over_allowance = max(
        -remaining_raw,
        0,
    )

    if allowance > 0:
        consumed_percentage = (
            float(used)
            / allowance
            * 100
        )

        remaining_percentage = max(
            100
            - consumed_percentage,
            0,
        )
    else:
        consumed_percentage = None
        remaining_percentage = None

    result.update(
        {
            "allowance": _round_value(
                allowance,
                usage_type,
            ),
            "remaining": _round_value(
                remaining,
                usage_type,
            ),
            "over_allowance": _round_value(
                over_allowance,
                usage_type,
            ),
            "consumed_percentage": (
                round(
                    consumed_percentage,
                    1,
                )
                if consumed_percentage
                is not None
                else None
            ),
            "remaining_percentage": (
                round(
                    remaining_percentage,
                    1,
                )
                if remaining_percentage
                is not None
                else None
            ),
        }
    )

    return result


def _single_usage(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    usage_type: UsageType,
    time_range: TimeRange | None = None,
    month: int | None = None,
    year: int | None = None,
    plan_type: str | None = None,
) -> TruthResult[dict]:
    period, error = _resolve_period(
        time_range=time_range,
        month=month,
        year=year,
    )

    if error is not None:
        return error

    plan, plan_error = resolve_usage_plan_row(
        db,
        customer.customer_id,
        plan_type=plan_type,
    )

    if plan_error is not None:
        return plan_error

    assert plan is not None

    try:
        totals = _get_period_totals(
            db,
            customer,
            period,
            subscription_id=plan["subscription_id"],
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve your "
                "usage information."
            ),
        )

    if plan is None:
        return not_found_result(
            source=source_for_table(
                "subscriptions"
            ),
            message=(
                "No subscription information "
                "was found for your account."
            ),
        )

    if not _is_applicable(
        plan,
        usage_type,
    ):
        return not_found_result(
            source=source_for_table(
                "usage"
            ),
            message=(
                f"{usage_type.value.title()} usage "
                "does not apply to your current "
                "fiber plan."
            ),
        )

    if totals["record_count"] == 0:
        return not_found_result(
            source=source_for_table(
                "usage"
            ),
            message=(
                "I don't have usage records for "
                f"{_period_label(period)}."
            ),
        )

    metric = _build_metric(
        plan=plan,
        totals=totals,
        usage_type=usage_type,
    )

    data = {
        "result_type": "USAGE_CURRENT",
        "subscription_id": plan[
            "subscription_id"
        ],
        "subscription_status": plan[
            "subscription_status"
        ],
        "plan_id": plan["plan_id"],
        "plan_name": plan[
            "plan_name"
        ],
        "plan_type": plan[
            "plan_type"
        ],
        "period": _period_label(
            period
        ),
        "start_date": (
            period.start_date.isoformat()
        ),
        "end_date": (
            period.end_date.isoformat()
        ),
        **metric,
    }

    return verified_result(
        data,
        source=source_for_table(
            "usage"
        ),
    )


def get_data_usage(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    time_range: TimeRange | None = None,
    month: int | None = None,
    year: int | None = None,
    plan_type: str | None = None,
) -> TruthResult[dict]:
    return _single_usage(
        db,
        customer,
        usage_type=UsageType.DATA,
        time_range=time_range,
        month=month,
        year=year,
        plan_type=plan_type,
    )


def get_voice_usage(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    time_range: TimeRange | None = None,
    month: int | None = None,
    year: int | None = None,
    plan_type: str | None = None,
) -> TruthResult[dict]:
    return _single_usage(
        db,
        customer,
        usage_type=UsageType.VOICE,
        time_range=time_range,
        month=month,
        year=year,
        plan_type=plan_type,
    )


def get_sms_usage(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    time_range: TimeRange | None = None,
    month: int | None = None,
    year: int | None = None,
    plan_type: str | None = None,
) -> TruthResult[dict]:
    return _single_usage(
        db,
        customer,
        usage_type=UsageType.SMS,
        time_range=time_range,
        month=month,
        year=year,
        plan_type=plan_type,
    )


def get_usage_remaining(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    usage_type: UsageType,
    time_range: TimeRange | None = None,
    month: int | None = None,
    year: int | None = None,
) -> TruthResult[dict]:
    result = _single_usage(
        db,
        customer,
        usage_type=usage_type,
        time_range=time_range,
        month=month,
        year=year,
    )

    if not result.is_verified:
        return result

    data = dict(
        result.data
    )

    data[
        "result_type"
    ] = "USAGE_REMAINING"

    return verified_result(
        data,
        source=source_for_table(
            "usage"
        ),
    )


def get_usage_percentage(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    usage_type: UsageType,
    percentage_type: UsagePercentageType | None = None,
    time_range: TimeRange | None = None,
    month: int | None = None,
    year: int | None = None,
) -> TruthResult[dict]:
    result = _single_usage(
        db,
        customer,
        usage_type=usage_type,
        time_range=time_range,
        month=month,
        year=year,
    )

    if not result.is_verified:
        return result

    data = dict(
        result.data
    )

    data[
        "result_type"
    ] = "USAGE_PERCENTAGE"

    data[
        "percentage_type"
    ] = (
        percentage_type
        or UsagePercentageType.CONSUMED
    ).value

    return verified_result(
        data,
        source=source_for_table(
            "usage"
        ),
    )


def get_usage_summary(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    time_range: TimeRange | None = None,
    month: int | None = None,
    year: int | None = None,
) -> TruthResult[dict]:
    period, error = _resolve_period(
        time_range=time_range,
        month=month,
        year=year,
    )

    if error is not None:
        return error

    try:
        plan, plan_error = _get_plan(
            db,
            customer,
        )
        if plan_error is not None:
            return plan_error
        assert plan is not None

        totals = _get_period_totals(
            db,
            customer,
            period,
            subscription_id=plan["subscription_id"],
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve your "
                "usage summary."
            ),
        )

    if totals["record_count"] == 0:
        return not_found_result(
            source=source_for_table(
                "usage"
            ),
            message=(
                "I don't have usage records for "
                f"{_period_label(period)}."
            ),
        )

    metrics = [
        _build_metric(
            plan=plan,
            totals=totals,
            usage_type=UsageType.DATA,
        )
    ]

    if plan["plan_type"] != "FIBER":
        metrics.extend(
            [
                _build_metric(
                    plan=plan,
                    totals=totals,
                    usage_type=UsageType.VOICE,
                ),
                _build_metric(
                    plan=plan,
                    totals=totals,
                    usage_type=UsageType.SMS,
                ),
            ]
        )

    data = {
        "result_type": "USAGE_SUMMARY",
        "subscription_id": plan[
            "subscription_id"
        ],
        "subscription_status": plan[
            "subscription_status"
        ],
        "plan_id": plan[
            "plan_id"
        ],
        "plan_name": plan[
            "plan_name"
        ],
        "plan_type": plan[
            "plan_type"
        ],
        "period": _period_label(
            period
        ),
        "metrics": metrics,
    }

    return verified_result(
        data,
        source=source_for_table(
            "usage"
        ),
    )


def _history(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    usage_type: UsageType,
    month_count: int,
) -> TruthResult[dict]:
    try:
        rows = get_monthly_usage_totals(
            db,
            customer.customer_id,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve your "
                "usage history."
            ),
        )

    if not rows:
        return not_found_result(
            source=source_for_table(
                "usage"
            ),
            message=(
                "I don't have recorded usage "
                "history for your account."
            ),
        )

    selected = rows[
        -month_count:
    ]

    history = []

    for row in selected:
        history.append(
            {
                "period": _period_from_key(
                    row["period"]
                ),
                "period_key": row[
                    "period"
                ],
                "value": _round_value(
                    _metric_value(
                        row,
                        usage_type,
                    ),
                    usage_type,
                ),
                "unit": USAGE_CONFIG[
                    usage_type
                ]["unit"],
            }
        )

    return verified_result(
        {
            "result_type": "USAGE_HISTORY",
            "usage_type": usage_type.value,
            "month_count": len(
                history
            ),
            "history": history,
        },
        source=source_for_table(
            "usage"
        ),
    )


def get_usage_history(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    usage_type: UsageType,
    month_count: int | None = None,
) -> TruthResult[dict]:
    return _history(
        db,
        customer,
        usage_type=usage_type,
        month_count=(
            month_count
            if month_count is not None
            else 6
        ),
    )


def get_usage_average(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    usage_type: UsageType,
    month_count: int | None = None,
) -> TruthResult[dict]:
    history_result = _history(
        db,
        customer,
        usage_type=usage_type,
        month_count=(
            month_count
            if month_count is not None
            else 6
        ),
    )

    if not history_result.is_verified:
        return history_result

    history = history_result.data[
        "history"
    ]

    average = mean(
        float(item["value"])
        for item in history
    )

    return verified_result(
        {
            "result_type": "USAGE_AVERAGE",
            "usage_type": usage_type.value,
            "month_count": len(
                history
            ),
            "average": _round_value(
                average,
                usage_type,
            ),
            "unit": USAGE_CONFIG[
                usage_type
            ]["unit"],
            "history": history,
        },
        source=source_for_table(
            "usage"
        ),
    )


def get_usage_extreme(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    usage_type: UsageType,
    extreme_type: UsageExtremeType,
    month_count: int | None = None,
) -> TruthResult[dict]:
    history_result = _history(
        db,
        customer,
        usage_type=usage_type,
        month_count=(
            month_count
            if month_count is not None
            else 6
        ),
    )

    if not history_result.is_verified:
        return history_result

    history = history_result.data[
        "history"
    ]

    if extreme_type == UsageExtremeType.HIGHEST:
        selected = max(
            history,
            key=lambda item: float(
                item["value"]
            ),
        )
    else:
        selected = min(
            history,
            key=lambda item: float(
                item["value"]
            ),
        )

    return verified_result(
        {
            "result_type": "USAGE_EXTREME",
            "usage_type": usage_type.value,
            "extreme_type": extreme_type.value,
            "period": selected[
                "period"
            ],
            "value": selected[
                "value"
            ],
            "unit": selected[
                "unit"
            ],
            "month_count": len(
                history
            ),
        },
        source=source_for_table(
            "usage"
        ),
    )


def get_usage_comparison(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    usage_type: UsageType,
    month: int | None = None,
    year: int | None = None,
    comparison_month: int | None = None,
    comparison_year: int | None = None,
) -> TruthResult[dict]:
    today = date.today()

    if month is not None:
        primary_year = (
            year
            if year is not None
            else today.year
        )

        primary_start = date(
            primary_year,
            month,
            1,
        )
    else:
        primary_start = date(
            today.year,
            today.month,
            1,
        )

    if comparison_month is not None:
        comparison_start = date(
            (
                comparison_year
                if comparison_year is not None
                else primary_start.year
            ),
            comparison_month,
            1,
        )
    else:
        comparison_start = shift_month(
            primary_start,
            -1,
        )

    primary_period = month_date_range(
        year=primary_start.year,
        month=primary_start.month,
    )

    comparison_period = month_date_range(
        year=comparison_start.year,
        month=comparison_start.month,
    )

    try:
        plan, plan_error = _get_plan(
            db,
            customer,
        )
        if plan_error is not None:
            return plan_error
        assert plan is not None

        primary = _get_period_totals(
            db,
            customer,
            primary_period,
            subscription_id=plan["subscription_id"],
        )

        comparison = _get_period_totals(
            db,
            customer,
            comparison_period,
            subscription_id=plan["subscription_id"],
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to compare your "
                "usage information."
            ),
        )

    if primary["record_count"] == 0:
        return not_found_result(
            source=source_for_table(
                "usage"
            ),
            message=(
                "I don't have usage records for "
                f"{_period_label(primary_period)}."
            ),
        )

    if comparison["record_count"] == 0:
        return not_found_result(
            source=source_for_table(
                "usage"
            ),
            message=(
                "I don't have usage records for "
                f"{_period_label(comparison_period)}."
            ),
        )

    primary_value = _metric_value(
        primary,
        usage_type,
    )

    comparison_value = _metric_value(
        comparison,
        usage_type,
    )

    difference = (
        primary_value
        - comparison_value
    )

    if difference > 0:
        direction = "INCREASE"
    elif difference < 0:
        direction = "DECREASE"
    else:
        direction = "NO_CHANGE"

    percentage_change = None

    if comparison_value != 0:
        percentage_change = round(
            (
                difference
                / comparison_value
            )
            * 100,
            1,
        )

    return verified_result(
        {
            "result_type": "USAGE_COMPARISON",
            "usage_type": usage_type.value,
            "period_1": _period_label(
                primary_period
            ),
            "period_1_usage": _round_value(
                primary_value,
                usage_type,
            ),
            "period_2": _period_label(
                comparison_period
            ),
            "period_2_usage": _round_value(
                comparison_value,
                usage_type,
            ),
            "absolute_difference": _round_value(
                abs(difference),
                usage_type,
            ),
            "signed_difference": _round_value(
                difference,
                usage_type,
            ),
            "percentage_change": (
                percentage_change
            ),
            "direction": direction,
            "unit": USAGE_CONFIG[
                usage_type
            ]["unit"],
        },
        source=source_for_table(
            "usage"
        ),
    )


def get_usage_trend(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    usage_type: UsageType,
    month_count: int | None = None,
) -> TruthResult[dict]:
    history_result = _history(
        db,
        customer,
        usage_type=usage_type,
        month_count=(
            month_count
            if month_count is not None
            else 6
        ),
    )

    if not history_result.is_verified:
        return history_result

    history = history_result.data[
        "history"
    ]

    if len(history) < 2:
        return validation_error_result(
            message=(
                "At least two months of usage "
                "history are required to determine "
                "a trend."
            ),
        )

    values = [
        float(item["value"])
        for item in history
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
        first = values[0]
        last = values[-1]

        if last > first:
            trend = "GENERALLY_INCREASING"
        elif last < first:
            trend = "GENERALLY_DECREASING"
        else:
            trend = "STABLE"

    return verified_result(
        {
            "result_type": "USAGE_TREND",
            "usage_type": usage_type.value,
            "trend": trend,
            "first_period": history[
                0
            ]["period"],
            "first_value": history[
                0
            ]["value"],
            "last_period": history[
                -1
            ]["period"],
            "last_value": history[
                -1
            ]["value"],
            "unit": USAGE_CONFIG[
                usage_type
            ]["unit"],
            "month_count": len(
                history
            ),
            "history": history,
        },
        source=source_for_table(
            "usage"
        ),
    )