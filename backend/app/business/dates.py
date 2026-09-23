"""Deterministic date and time-range resolution for NexaTel.

The LLM may identify a user's requested time range, but this module is
responsible for converting that semantic value into concrete dates.

Supported ranges:
- CURRENT_MONTH
- LAST_MONTH
- CURRENT_YEAR

All returned ranges are inclusive.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.models.domain import TimeRange


@dataclass(frozen=True)
class DateRange:
    """Concrete inclusive date range."""

    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.start_date > self.end_date:
            raise ValueError("start_date cannot be after end_date")


def first_day_of_month(value: date) -> date:
    """Return the first day of the month containing value."""

    return value.replace(day=1)


def last_day_of_month(value: date) -> date:
    """Return the last day of the month containing value."""

    if value.month == 12:
        next_month = date(value.year + 1, 1, 1)
    else:
        next_month = date(value.year, value.month + 1, 1)

    return next_month - timedelta(days=1)


def resolve_time_range(
    time_range: TimeRange,
    *,
    reference_date: date | None = None,
) -> DateRange:
    """Resolve a supported semantic time range into concrete dates.

    Args:
        time_range: Supported NexaTel time-range value.
        reference_date: Optional date used as the current date.
            Supplying this makes the function deterministic in tests.

    Returns:
        A concrete inclusive DateRange.

    Raises:
        ValueError: If the time range is unsupported.
    """

    current_date = reference_date or date.today()

    if time_range == TimeRange.CURRENT_MONTH:
        return DateRange(
            start_date=first_day_of_month(current_date),
            end_date=last_day_of_month(current_date),
        )

    if time_range == TimeRange.LAST_MONTH:
        first_current_month = first_day_of_month(current_date)
        last_previous_month = first_current_month - timedelta(days=1)

        return DateRange(
            start_date=first_day_of_month(last_previous_month),
            end_date=last_previous_month,
        )

    if time_range == TimeRange.CURRENT_YEAR:
        return DateRange(
            start_date=date(current_date.year, 1, 1),
            end_date=date(current_date.year, 12, 31),
        )

    raise ValueError(f"Unsupported time range: {time_range}")


def resolve_optional_time_range(
    time_range: TimeRange | None,
    *,
    reference_date: date | None = None,
) -> DateRange | None:
    """Resolve an optional time range.

    Returns None when no time range was supplied.
    """

    if time_range is None:
        return None

    return resolve_time_range(
        time_range,
        reference_date=reference_date,
    )