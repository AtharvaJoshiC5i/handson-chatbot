"""Handlers for NexaTel usage intents."""

from __future__ import annotations

import sqlite3

from app.business.dates import resolve_time_range
from app.business.validation import validate_time_range
from app.database.queries.usage import (
    get_usage_by_customer_and_date_range,
)
from app.models.domain import CustomerContext, TimeRange
from app.truth.result import (
    TruthResult,
    database_error_result,
    not_found_result,
    validation_error_result,
    verified_result,
)
from app.truth.sources import source_for_table


def _resolve_required_range(
    time_range: TimeRange | None,
) -> tuple[object | None, TruthResult[None] | None]:
    """Resolve and validate a required usage time range."""

    try:
        validated = validate_time_range(
            time_range,
            required=True,
        )

        date_range = resolve_time_range(
            validated,
        )

        return date_range, None

    except ValueError as exc:
        return None, validation_error_result(
            message=str(exc),
        )


def _get_usage(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    time_range: TimeRange | None,
    usage_type: str,
) -> TruthResult[dict]:
    """Retrieve one usage category for the authenticated customer."""

    date_range, error = _resolve_required_range(time_range)

    if error is not None:
        return error

    try:
        rows = get_usage_by_customer_and_date_range(
            db,
            customer_id=customer.customer_id,
            start_date=date_range.start_date.isoformat(),
            end_date=date_range.end_date.isoformat(),
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve your usage information.",
        )

    matching_rows = [
        row
        for row in rows
        if row["usage_type"] == usage_type
    ]

    if not matching_rows:
        return not_found_result(
            source=source_for_table("usage"),
            message=(
                f"No {usage_type.lower()} usage data was found "
                "for the requested period."
            ),
        )

    total_usage = sum(
        float(row["amount"])
        for row in matching_rows
    )

    unit = matching_rows[0]["unit"]

    data = {
        "usage_type": usage_type,
        "time_range": time_range.value,
        "start_date": date_range.start_date.isoformat(),
        "end_date": date_range.end_date.isoformat(),
        "total_usage": total_usage,
        "unit": unit,
        "records": [dict(row) for row in matching_rows],
    }

    return verified_result(
        data,
        source=source_for_table("usage"),
    )


def get_data_usage(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    time_range: TimeRange | None,
) -> TruthResult[dict]:
    """Return data usage for the requested period."""

    return _get_usage(
        db,
        customer,
        time_range=time_range,
        usage_type="DATA",
    )


def get_voice_usage(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    time_range: TimeRange | None,
) -> TruthResult[dict]:
    """Return voice usage for the requested period."""

    return _get_usage(
        db,
        customer,
        time_range=time_range,
        usage_type="VOICE",
    )