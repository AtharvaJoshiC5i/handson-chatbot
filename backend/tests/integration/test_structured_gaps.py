"""Integration tests for structured-data gap features."""

from __future__ import annotations

import sqlite3

import pytest

from app.database.seed import seed_database
from app.handlers.billing_extras import (
    get_bill_charge_summary,
    get_projected_bill,
)
from app.handlers.payment_profile import (
    get_account_credits,
    get_payment_profile_status,
)
from app.handlers.subscriptions_catalog import (
    get_list_subscriptions,
    get_plan_catalog,
)
from app.models.domain import (
    CustomerContext,
    TruthStatus,
)


@pytest.fixture
def db() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    seed_database(connection, reset=True)
    try:
        yield connection
    finally:
        connection.close()


def test_list_subscriptions_for_multi_service_customer(
    db: sqlite3.Connection,
) -> None:
    result = get_list_subscriptions(
        db,
        CustomerContext(customer_id="CUST003"),
    )

    assert result.status == TruthStatus.VERIFIED
    assert result.data is not None
    assert result.data["count"] >= 2
    plan_types = {
        item["plan_type"]
        for item in result.data["subscriptions"]
    }
    assert plan_types >= {"MOBILE", "FIBER"}


def test_plan_catalog_returns_plans(
    db: sqlite3.Connection,
) -> None:
    result = get_plan_catalog(
        db,
        CustomerContext(customer_id="CUST001"),
        plan_type="FIBER",
    )

    assert result.status == TruthStatus.VERIFIED
    assert result.data is not None
    assert all(
        plan["plan_type"] == "FIBER"
        for plan in result.data["plans"]
    )


def test_roaming_charge_summary_for_demo_customer(
    db: sqlite3.Connection,
) -> None:
    result = get_bill_charge_summary(
        db,
        CustomerContext(customer_id="CUST002"),
        bill_item_type="ROAMING",
        month_count=6,
    )

    assert result.status == TruthStatus.VERIFIED
    assert result.data is not None
    assert result.data["total_amount"] > 0


def test_payment_profile_and_credits(
    db: sqlite3.Connection,
) -> None:
    profile = get_payment_profile_status(
        db,
        CustomerContext(customer_id="CUST002"),
    )
    credits = get_account_credits(
        db,
        CustomerContext(customer_id="CUST002"),
    )

    assert profile.status == TruthStatus.VERIFIED
    assert profile.data is not None
    assert profile.data["autopay_enabled"] is False

    assert credits.status == TruthStatus.VERIFIED
    assert credits.data is not None
    assert credits.data["available_total"] > 0


def test_projected_bill_returns_estimate(
    db: sqlite3.Connection,
) -> None:
    result = get_projected_bill(
        db,
        CustomerContext(customer_id="CUST005"),
    )

    assert result.status == TruthStatus.VERIFIED
    assert result.data is not None
    assert result.data["estimated_amount"] > 0
