from __future__ import annotations

import sqlite3

import pytest

from app.database.seed import seed_database
from app.handlers.usage import (
    get_data_usage,
    get_usage_average,
    get_usage_comparison,
    get_usage_extreme,
    get_usage_history,
    get_usage_percentage,
    get_usage_remaining,
    get_usage_summary,
    get_usage_trend,
    get_voice_usage,
)
from app.models.domain import (
    CustomerContext,
    TruthStatus,
    UsageExtremeType,
    UsagePercentageType,
    UsageType,
)


def _db() -> sqlite3.Connection:
    """Create a fresh deterministic Phase 0 database."""

    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row

    db.execute(
        "PRAGMA foreign_keys = ON"
    )

    seed_database(
        db,
        reset=True,
    )

    return db


@pytest.fixture
def db() -> sqlite3.Connection:
    connection = _db()

    try:
        yield connection
    finally:
        connection.close()


def _customer(
    customer_id: str,
) -> CustomerContext:
    return CustomerContext(
        customer_id=customer_id
    )


def _verified_data(result):
    assert result.status == TruthStatus.VERIFIED
    assert result.data is not None

    return result.data


# ============================================================
# CURRENT USAGE
# ============================================================


def test_named_month_data_usage_is_aggregated(
    db: sqlite3.Connection,
):
    """
    CUST006 is the deliberate heavy-usage demo customer.

    September total in the Phase 0 canonical dataset = 94 GB.
    """

    result = get_data_usage(
        db,
        _customer("CUST006"),
        month=9,
        year=2026,
    )

    data = _verified_data(result)

    assert data["usage_type"] == "DATA"
    assert data["period"] == "September 2026"
    assert data["used"] == pytest.approx(
        94.0,
        abs=0.01,
    )

    assert data["allowance"] == pytest.approx(
        100.0
    )

    assert data["remaining"] == pytest.approx(
        6.0
    )


def test_named_month_voice_usage_is_aggregated(
    db: sqlite3.Connection,
):
    result = get_voice_usage(
        db,
        _customer("CUST006"),
        month=9,
        year=2026,
    )

    data = _verified_data(result)

    assert data["usage_type"] == "VOICE"
    assert data["period"] == "September 2026"

    assert data["used"] > 0
    assert data["allowance"] == 3000
    assert data["remaining"] >= 0


def test_named_month_sms_usage_via_summary(
    db: sqlite3.Connection,
):
    result = get_usage_summary(
        db,
        _customer("CUST006"),
        month=9,
        year=2026,
    )

    data = _verified_data(result)

    sms = next(
        metric
        for metric in data["metrics"]
        if metric["usage_type"] == "SMS"
    )

    assert sms["used"] > 0
    assert sms["allowance"] == 300
    assert sms["remaining"] >= 0


# ============================================================
# REMAINING ALLOWANCE
# ============================================================


def test_data_remaining(
    db: sqlite3.Connection,
):
    result = get_usage_remaining(
        db,
        _customer("CUST006"),
        usage_type=UsageType.DATA,
        month=9,
        year=2026,
    )

    data = _verified_data(result)

    assert data["used"] == pytest.approx(
        94.0,
        abs=0.01,
    )

    assert data["allowance"] == pytest.approx(
        100.0
    )

    assert data["remaining"] == pytest.approx(
        6.0
    )

    assert data["over_allowance"] == 0


def test_voice_remaining(
    db: sqlite3.Connection,
):
    result = get_usage_remaining(
        db,
        _customer("CUST006"),
        usage_type=UsageType.VOICE,
        month=9,
        year=2026,
    )

    data = _verified_data(result)

    assert data["allowance"] == 3000
    assert data["used"] > 0

    assert (
        data["remaining"]
        == data["allowance"] - data["used"]
    )


def test_sms_remaining(
    db: sqlite3.Connection,
):
    result = get_usage_remaining(
        db,
        _customer("CUST006"),
        usage_type=UsageType.SMS,
        month=9,
        year=2026,
    )

    data = _verified_data(result)

    assert data["allowance"] == 300
    assert data["used"] > 0

    assert (
        data["remaining"]
        == data["allowance"] - data["used"]
    )


# ============================================================
# PERCENTAGES
# ============================================================


def test_consumed_percentage(
    db: sqlite3.Connection,
):
    result = get_usage_percentage(
        db,
        _customer("CUST006"),
        usage_type=UsageType.DATA,
        percentage_type=(
            UsagePercentageType.CONSUMED
        ),
        month=9,
        year=2026,
    )

    data = _verified_data(result)

    assert data["used"] == pytest.approx(
        94.0,
        abs=0.01,
    )

    assert data["allowance"] == 100

    assert data[
        "consumed_percentage"
    ] == pytest.approx(
        94.0,
        abs=0.1,
    )


def test_remaining_percentage(
    db: sqlite3.Connection,
):
    result = get_usage_percentage(
        db,
        _customer("CUST006"),
        usage_type=UsageType.DATA,
        percentage_type=(
            UsagePercentageType.REMAINING
        ),
        month=9,
        year=2026,
    )

    data = _verified_data(result)

    assert data[
        "remaining_percentage"
    ] == pytest.approx(
        6.0,
        abs=0.1,
    )


# ============================================================
# MOBILE SUMMARY
# ============================================================


def test_mobile_usage_summary_contains_all_metrics(
    db: sqlite3.Connection,
):
    result = get_usage_summary(
        db,
        _customer("CUST006"),
        month=9,
        year=2026,
    )

    data = _verified_data(result)

    assert data["plan_type"] == "MOBILE"

    usage_types = {
        metric["usage_type"]
        for metric in data["metrics"]
    }

    assert usage_types == {
        "DATA",
        "VOICE",
        "SMS",
    }


# ============================================================
# FIBER / UNLIMITED
# ============================================================


def test_fiber_summary_contains_only_data(
    db: sqlite3.Connection,
):
    result = get_usage_summary(
        db,
        _customer("CUST003"),
        month=9,
        year=2026,
    )

    data = _verified_data(result)

    assert data["plan_type"] == "FIBER"

    assert len(
        data["metrics"]
    ) == 1

    metric = data["metrics"][0]

    assert metric["usage_type"] == "DATA"
    assert metric["is_unlimited"] is True


def test_unlimited_plan_has_no_remaining_cap(
    db: sqlite3.Connection,
):
    result = get_usage_remaining(
        db,
        _customer("CUST003"),
        usage_type=UsageType.DATA,
        month=9,
        year=2026,
    )

    data = _verified_data(result)

    assert data["is_unlimited"] is True
    assert data["allowance"] is None
    assert data["remaining"] is None

    assert (
        data["consumed_percentage"]
        is None
    )

    assert (
        data["remaining_percentage"]
        is None
    )


def test_unlimited_plan_does_not_divide_by_zero(
    db: sqlite3.Connection,
):
    result = get_usage_percentage(
        db,
        _customer("CUST003"),
        usage_type=UsageType.DATA,
        percentage_type=(
            UsagePercentageType.CONSUMED
        ),
        month=9,
        year=2026,
    )

    data = _verified_data(result)

    assert data["is_unlimited"] is True

    assert (
        data["consumed_percentage"]
        is None
    )


def test_voice_usage_not_applicable_to_fiber(
    db: sqlite3.Connection,
):
    result = get_voice_usage(
        db,
        _customer("CUST003"),
        month=9,
        year=2026,
    )

    assert result.status == TruthStatus.NOT_FOUND


# ============================================================
# HISTORICAL USAGE
# ============================================================


def test_named_historical_month(
    db: sqlite3.Connection,
):
    result = get_data_usage(
        db,
        _customer("CUST006"),
        month=8,
        year=2026,
    )

    data = _verified_data(result)

    assert data["period"] == "August 2026"

    assert data["used"] == pytest.approx(
        88.0,
        abs=0.01,
    )


def test_heavy_customer_six_month_history(
    db: sqlite3.Connection,
):
    result = get_usage_history(
        db,
        _customer("CUST006"),
        usage_type=UsageType.DATA,
        month_count=6,
    )

    data = _verified_data(result)

    history = data["history"]

    assert len(history) == 6

    assert [
        item["period_key"]
        for item in history
    ] == [
        "2026-04",
        "2026-05",
        "2026-06",
        "2026-07",
        "2026-08",
        "2026-09",
    ]

    assert [
        item["value"]
        for item in history
    ] == pytest.approx(
        [
            61,
            68,
            74,
            81,
            88,
            94,
        ],
        abs=0.01,
    )


def test_last_three_available_months(
    db: sqlite3.Connection,
):
    result = get_usage_history(
        db,
        _customer("CUST006"),
        usage_type=UsageType.DATA,
        month_count=3,
    )

    data = _verified_data(result)

    history = data["history"]

    assert len(history) == 3

    assert [
        item["period_key"]
        for item in history
    ] == [
        "2026-07",
        "2026-08",
        "2026-09",
    ]

    assert [
        item["value"]
        for item in history
    ] == pytest.approx(
        [
            81,
            88,
            94,
        ],
        abs=0.01,
    )


# ============================================================
# COMPARISON
# ============================================================


def test_named_month_comparison_increase(
    db: sqlite3.Connection,
):
    result = get_usage_comparison(
        db,
        _customer("CUST006"),
        usage_type=UsageType.DATA,
        month=9,
        year=2026,
        comparison_month=8,
        comparison_year=2026,
    )

    data = _verified_data(result)

    assert data["period_1"] == "September 2026"
    assert data["period_2"] == "August 2026"

    assert data[
        "period_1_usage"
    ] == pytest.approx(
        94.0,
        abs=0.01,
    )

    assert data[
        "period_2_usage"
    ] == pytest.approx(
        88.0,
        abs=0.01,
    )

    assert data[
        "absolute_difference"
    ] == pytest.approx(
        6.0,
        abs=0.01,
    )

    assert data["direction"] == "INCREASE"

    assert data[
        "percentage_change"
    ] == pytest.approx(
        6.8,
        abs=0.1,
    )


def test_decreasing_customer_comparison(
    db: sqlite3.Connection,
):
    """
    CUST018 uses the deliberate declining usage pattern.
    """

    result = get_usage_comparison(
        db,
        _customer("CUST018"),
        usage_type=UsageType.DATA,
        month=9,
        year=2026,
        comparison_month=8,
        comparison_year=2026,
    )

    data = _verified_data(result)

    assert data["direction"] == "DECREASE"

    assert (
        data["period_1_usage"]
        < data["period_2_usage"]
    )


def test_stable_customer_can_compare_months(
    db: sqlite3.Connection,
):
    result = get_usage_comparison(
        db,
        _customer("CUST005"),
        usage_type=UsageType.DATA,
        month=9,
        year=2026,
        comparison_month=8,
        comparison_year=2026,
    )

    data = _verified_data(result)

    assert data["period_1"] == "September 2026"
    assert data["period_2"] == "August 2026"

    assert data[
        "period_1_usage"
    ] == pytest.approx(
        data["period_2_usage"],
        abs=0.01,
    )

    assert data["direction"] == "NO_CHANGE"


# ============================================================
# AVERAGE
# ============================================================


def test_average_uses_monthly_totals(
    db: sqlite3.Connection,
):
    result = get_usage_average(
        db,
        _customer("CUST006"),
        usage_type=UsageType.DATA,
        month_count=6,
    )

    data = _verified_data(result)

    expected = (
        61
        + 68
        + 74
        + 81
        + 88
        + 94
    ) / 6

    assert data["average"] == pytest.approx(
        round(expected, 2),
        abs=0.01,
    )

    assert data["month_count"] == 6


# ============================================================
# HIGHEST / LOWEST
# ============================================================


def test_highest_usage_month(
    db: sqlite3.Connection,
):
    result = get_usage_extreme(
        db,
        _customer("CUST006"),
        usage_type=UsageType.DATA,
        extreme_type=(
            UsageExtremeType.HIGHEST
        ),
        month_count=6,
    )

    data = _verified_data(result)

    assert data["period"] == "September 2026"

    assert data["value"] == pytest.approx(
        94.0,
        abs=0.01,
    )


def test_lowest_usage_month(
    db: sqlite3.Connection,
):
    result = get_usage_extreme(
        db,
        _customer("CUST006"),
        usage_type=UsageType.DATA,
        extreme_type=(
            UsageExtremeType.LOWEST
        ),
        month_count=6,
    )

    data = _verified_data(result)

    assert data["period"] == "April 2026"

    assert data["value"] == pytest.approx(
        61.0,
        abs=0.01,
    )


# ============================================================
# TREND
# ============================================================


def test_increasing_usage_trend(
    db: sqlite3.Connection,
):
    result = get_usage_trend(
        db,
        _customer("CUST006"),
        usage_type=UsageType.DATA,
        month_count=6,
    )

    data = _verified_data(result)

    assert (
        data["trend"]
        == "GENERALLY_INCREASING"
    )

    assert data["first_period"] == "April 2026"
    assert data["last_period"] == "September 2026"

    assert data["first_value"] == pytest.approx(
        61.0,
        abs=0.01,
    )

    assert data["last_value"] == pytest.approx(
        94.0,
        abs=0.01,
    )


def test_decreasing_usage_trend(
    db: sqlite3.Connection,
):
    result = get_usage_trend(
        db,
        _customer("CUST018"),
        usage_type=UsageType.DATA,
        month_count=6,
    )

    data = _verified_data(result)

    assert (
        data["trend"]
        == "GENERALLY_DECREASING"
    )


# ============================================================
# OVER ALLOWANCE
# ============================================================


def test_over_allowance_never_returns_negative_remaining(
    db: sqlite3.Connection,
):
    """
    Insert a deterministic over-allowance month specifically to
    verify Phase 1's overage behavior.
    """

    db.execute(
        """
        INSERT INTO usage (
            usage_id,
            customer_id,
            subscription_id,
            usage_date,
            data_used_gb,
            voice_minutes,
            sms_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "USE_OVERAGE_TEST",
            "CUST001",
            "SUB001",
            "2026-10-05",
            80.0,
            0,
            0,
        ),
    )

    db.commit()

    result = get_usage_remaining(
        db,
        _customer("CUST001"),
        usage_type=UsageType.DATA,
        month=10,
        year=2026,
    )

    data = _verified_data(result)

    assert data["allowance"] == 75
    assert data["used"] == 80

    assert data["remaining"] == 0

    assert data["over_allowance"] == 5

    assert data[
        "consumed_percentage"
    ] > 100


# ============================================================
# MISSING DATA
# ============================================================


def test_missing_month_is_not_treated_as_zero(
    db: sqlite3.Connection,
):
    result = get_data_usage(
        db,
        _customer("CUST006"),
        month=1,
        year=2026,
    )

    assert result.status == TruthStatus.NOT_FOUND

    assert result.message is not None

    assert "don't have usage records" in (
        result.message.lower()
    )


# ============================================================
# CANCELLED CUSTOMER
# ============================================================


def test_cancelled_customer_can_query_historical_usage(
    db: sqlite3.Connection,
):
    result = get_data_usage(
        db,
        _customer("CUST007"),
        month=7,
        year=2026,
    )

    data = _verified_data(result)

    assert data["period"] == "July 2026"

    assert (
        data["subscription_status"]
        == "CANCELLED"
    )


def test_cancelled_customer_has_no_post_cancellation_usage(
    db: sqlite3.Connection,
):
    result = get_data_usage(
        db,
        _customer("CUST007"),
        month=9,
        year=2026,
    )

    assert result.status == TruthStatus.NOT_FOUND


# ============================================================
# CUSTOMER ISOLATION
# ============================================================


def test_usage_is_scoped_to_authenticated_customer(
    db: sqlite3.Connection,
):
    customer_5 = get_data_usage(
        db,
        _customer("CUST005"),
        month=9,
        year=2026,
    )

    customer_6 = get_data_usage(
        db,
        _customer("CUST006"),
        month=9,
        year=2026,
    )

    data_5 = _verified_data(
        customer_5
    )

    data_6 = _verified_data(
        customer_6
    )

    assert data_5["used"] != data_6["used"]

    assert data_6["used"] == pytest.approx(
        94.0,
        abs=0.01,
    )


# ============================================================
# RAW DATABASE CROSS-CHECKS
# ============================================================


def test_handler_matches_raw_database_aggregation(
    db: sqlite3.Connection,
):
    raw = db.execute(
        """
        SELECT
            SUM(data_used_gb)
        FROM usage
        WHERE customer_id = ?
          AND usage_date >= ?
          AND usage_date <= ?
        """,
        (
            "CUST006",
            "2026-09-01",
            "2026-09-30",
        ),
    ).fetchone()[0]

    result = get_data_usage(
        db,
        _customer("CUST006"),
        month=9,
        year=2026,
    )

    data = _verified_data(result)

    assert data["used"] == pytest.approx(
        raw,
        abs=0.01,
    )


def test_average_matches_raw_monthly_aggregation(
    db: sqlite3.Connection,
):
    raw_rows = db.execute(
        """
        SELECT
            substr(usage_date, 1, 7) AS period,
            SUM(data_used_gb) AS total
        FROM usage
        WHERE customer_id = ?
        GROUP BY substr(usage_date, 1, 7)
        ORDER BY period
        """,
        ("CUST006",),
    ).fetchall()

    expected = sum(
        row["total"]
        for row in raw_rows
    ) / len(raw_rows)

    result = get_usage_average(
        db,
        _customer("CUST006"),
        usage_type=UsageType.DATA,
        month_count=6,
    )

    data = _verified_data(result)

    assert data["average"] == pytest.approx(
        expected,
        abs=0.01,
    )