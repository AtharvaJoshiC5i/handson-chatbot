"""Unit tests for NexaTel date business logic."""

from datetime import date

import pytest

from app.business.dates import (
    DateRange,
    first_day_of_month,
    last_day_of_month,
    resolve_optional_time_range,
    resolve_time_range,
)
from app.models.domain import TimeRange


def test_first_day_of_month() -> None:
    result = first_day_of_month(date(2026, 9, 22))

    assert result == date(2026, 9, 1)


def test_last_day_of_month_for_30_day_month() -> None:
    result = last_day_of_month(date(2026, 9, 22))

    assert result == date(2026, 9, 30)


def test_last_day_of_month_for_february_non_leap_year() -> None:
    result = last_day_of_month(date(2026, 2, 15))

    assert result == date(2026, 2, 28)


def test_last_day_of_month_for_february_leap_year() -> None:
    result = last_day_of_month(date(2028, 2, 15))

    assert result == date(2028, 2, 29)


def test_last_day_of_december() -> None:
    result = last_day_of_month(date(2026, 12, 10))

    assert result == date(2026, 12, 31)


def test_current_month_resolution() -> None:
    result = resolve_time_range(
        TimeRange.CURRENT_MONTH,
        reference_date=date(2026, 9, 22),
    )

    assert result == DateRange(
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
    )


def test_last_month_resolution() -> None:
    result = resolve_time_range(
        TimeRange.LAST_MONTH,
        reference_date=date(2026, 9, 22),
    )

    assert result == DateRange(
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
    )


def test_current_year_resolution() -> None:
    result = resolve_time_range(
        TimeRange.CURRENT_YEAR,
        reference_date=date(2026, 9, 22),
    )

    assert result == DateRange(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )


def test_current_month_at_year_boundary() -> None:
    result = resolve_time_range(
        TimeRange.CURRENT_MONTH,
        reference_date=date(2026, 1, 5),
    )

    assert result == DateRange(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )


def test_last_month_at_year_boundary() -> None:
    result = resolve_time_range(
        TimeRange.LAST_MONTH,
        reference_date=date(2026, 1, 5),
    )

    assert result == DateRange(
        start_date=date(2025, 12, 1),
        end_date=date(2025, 12, 31),
    )


def test_optional_time_range_returns_none() -> None:
    result = resolve_optional_time_range(
        None,
        reference_date=date(2026, 9, 22),
    )

    assert result is None


def test_optional_time_range_is_resolved() -> None:
    result = resolve_optional_time_range(
        TimeRange.CURRENT_MONTH,
        reference_date=date(2026, 9, 22),
    )

    assert result == DateRange(
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
    )


def test_invalid_date_range_raises_error() -> None:
    with pytest.raises(ValueError):
        DateRange(
            start_date=date(2026, 9, 30),
            end_date=date(2026, 9, 1),
        )