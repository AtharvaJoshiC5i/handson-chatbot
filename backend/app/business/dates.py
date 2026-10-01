"""Deterministic date and time-period resolution for NexaTel."""

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
            raise ValueError(
                "start_date cannot be after end_date"
            )


def first_day_of_month(
    value: date,
) -> date:
    return value.replace(day=1)


def last_day_of_month(
    value: date,
) -> date:
    if value.month == 12:
        next_month = date(
            value.year + 1,
            1,
            1,
        )
    else:
        next_month = date(
            value.year,
            value.month + 1,
            1,
        )

    return next_month - timedelta(days=1)


def previous_month(
    value: date,
) -> date:
    first_current = first_day_of_month(
        value
    )

    return first_current - timedelta(days=1)


def shift_month(
    value: date,
    offset: int,
) -> date:
    """
    Shift a date to the first day of another month.

    No third-party date dependency is required.
    """

    month_index = (
        value.year * 12
        + value.month
        - 1
        + offset
    )

    year = month_index // 12
    month = month_index % 12 + 1

    return date(
        year,
        month,
        1,
    )


def month_date_range(
    *,
    year: int,
    month: int,
) -> DateRange:
    """Resolve a concrete year/month into an inclusive range."""

    start = date(
        year,
        month,
        1,
    )

    return DateRange(
        start_date=start,
        end_date=last_day_of_month(start),
    )


def resolve_time_range(
    time_range: TimeRange,
    *,
    reference_date: date | None = None,
) -> DateRange:
    """
    Resolve a semantic time range.

    reference_date can be supplied by tests for deterministic behavior.
    """

    current_date = reference_date or date.today()

    if time_range == TimeRange.CURRENT_MONTH:
        return DateRange(
            start_date=first_day_of_month(
                current_date
            ),
            end_date=last_day_of_month(
                current_date
            ),
        )

    if time_range == TimeRange.LAST_MONTH:
        last_previous = previous_month(
            current_date
        )

        return DateRange(
            start_date=first_day_of_month(
                last_previous
            ),
            end_date=last_day_of_month(
                last_previous
            ),
        )

    if time_range == TimeRange.CURRENT_YEAR:
        return DateRange(
            start_date=date(
                current_date.year,
                1,
                1,
            ),
            end_date=date(
                current_date.year,
                12,
                31,
            ),
        )

    raise ValueError(
        f"Unsupported time range: {time_range}"
    )


def resolve_optional_time_range(
    time_range: TimeRange | None,
    *,
    reference_date: date | None = None,
) -> DateRange | None:
    if time_range is None:
        return None

    return resolve_time_range(
        time_range,
        reference_date=reference_date,
    )


def resolve_usage_period(
    *,
    time_range: TimeRange | None = None,
    month: int | None = None,
    year: int | None = None,
    reference_date: date | None = None,
) -> DateRange:
    """
    Resolve a usage period.

    Priority:
        explicit month/year
        semantic time range
        current month

    A named month without a year resolves to that month in the
    reference/current year.
    """

    current_date = reference_date or date.today()

    if month is not None:
        resolved_year = (
            year
            if year is not None
            else current_date.year
        )

        return month_date_range(
            year=resolved_year,
            month=month,
        )

    if year is not None:
        raise ValueError(
            "A year cannot be used without a month "
            "for a monthly usage request."
        )

    return resolve_time_range(
        time_range or TimeRange.CURRENT_MONTH,
        reference_date=current_date,
    )


def recent_month_ranges(
    month_count: int,
    *,
    reference_date: date | None = None,
) -> list[DateRange]:
    """
    Return chronological monthly ranges ending with the current month.
    """

    if month_count < 1:
        raise ValueError(
            "month_count must be at least 1."
        )

    current_date = (
        reference_date
        or date.today()
    )

    current_month = first_day_of_month(
        current_date
    )

    ranges: list[DateRange] = []

    for offset in range(
        -(month_count - 1),
        1,
    ):
        month_start = shift_month(
            current_month,
            offset,
        )

        ranges.append(
            DateRange(
                start_date=month_start,
                end_date=last_day_of_month(
                    month_start
                ),
            )
        )

    return ranges