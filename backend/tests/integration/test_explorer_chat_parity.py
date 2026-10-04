"""Explorer parity: each database table is reachable via chat handlers."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from typing import Any

import pytest

from app.database.seed import seed_database
from app.handlers.account import get_account_status
from app.handlers.billing import get_bill_history_for_customer
from app.handlers.devices import get_device_information
from app.handlers.explorer_parity import (
    list_bill_items,
    list_ticket_updates,
    list_usage_records_for_customer,
)
from app.handlers.payment_profile import (
    get_account_credits,
    get_payment_profile_status,
)
from app.handlers.payments import get_payment_history_for_customer
from app.handlers.plans import get_current_plan
from app.handlers.subscriptions_catalog import (
    get_plan_catalog,
    get_plan_details,
    get_list_subscriptions,
)
from app.handlers.support import get_customer_support_tickets
from app.models.domain import CustomerContext, TruthStatus
from app.services.data_explorer_service import TABLE_CONFIG


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


CUSTOMER = CustomerContext(customer_id="CUST002")


def _assert_verified(
    result: Any,
    *,
    table: str,
) -> None:
    assert result.status == TruthStatus.VERIFIED, (
        f"No verified handler for table '{table}'"
    )
    assert result.data is not None


# One primary chat path per explorer table (customer-scoped).
TABLE_HANDLERS: dict[
    str,
    Callable[[sqlite3.Connection], Any],
] = {
    "customers": lambda db: get_account_status(db, CUSTOMER),
    "plans": lambda db: get_plan_details(
        db,
        CUSTOMER,
        plan_id="PLAN001",
    ),
    "subscriptions": lambda db: get_list_subscriptions(
        db,
        CUSTOMER,
    ),
    "usage": lambda db: list_usage_records_for_customer(
        db,
        CUSTOMER,
        limit=5,
    ),
    "bills": lambda db: get_bill_history_for_customer(
        db,
        CUSTOMER,
        limit=3,
    ),
    "bill_items": lambda db: list_bill_items(
        db,
        CUSTOMER,
        limit=10,
    ),
    "payments": lambda db: get_payment_history_for_customer(
        db,
        CUSTOMER,
        limit=3,
    ),
    "support_tickets": lambda db: get_customer_support_tickets(
        db,
        CUSTOMER,
        limit=5,
    ),
    "support_ticket_updates": lambda db: list_ticket_updates(
        db,
        CUSTOMER,
        limit=10,
    ),
    "customer_payment_profiles": lambda db: get_payment_profile_status(
        db,
        CUSTOMER,
    ),
    "account_credits": lambda db: get_account_credits(
        db,
        CUSTOMER,
    ),
    "devices": lambda db: get_device_information(
        db,
        CUSTOMER,
    ),
}


def test_explorer_tables_match_config() -> None:
    assert set(TABLE_HANDLERS) == set(TABLE_CONFIG)


@pytest.mark.parametrize("table_name", sorted(TABLE_HANDLERS))
def test_each_table_has_verified_chat_handler(
    db: sqlite3.Connection,
    table_name: str,
) -> None:
    handler = TABLE_HANDLERS[table_name]
    result = handler(db)

    if table_name == "customer_payment_profiles":
        # CUST002 has a profile row in seed data.
        _assert_verified(result, table=table_name)
        return

    _assert_verified(result, table=table_name)


def test_plan_catalog_covers_plans_table_for_anonymous_catalog(
    db: sqlite3.Connection,
) -> None:
    result = get_plan_catalog(db, CUSTOMER)
    _assert_verified(result, table="plans")


def test_current_plan_with_mobile_type_for_multi_line(
    db: sqlite3.Connection,
) -> None:
    result = get_current_plan(
        db,
        CustomerContext(customer_id="CUST003"),
        plan_type="MOBILE",
    )
    _assert_verified(result, table="subscriptions")
    assert result.data["plan_type"] == "MOBILE"
