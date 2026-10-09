"""Billing period vs payment month alignment."""

from __future__ import annotations

import sqlite3
from datetime import date

from app.database.queries.bills import (
    get_current_statement_bill,
    get_latest_bill,
)
from app.database.seed import seed_database
from app.handlers.billing import get_current_bill
from app.handlers.cross_domain import get_bill_payment_status
from app.handlers.payments import get_payment_history_for_customer
from app.models.domain import CustomerContext, TruthStatus


def _db() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    seed_database(connection, reset=True)
    return connection


def test_current_statement_on_oct_8_is_september_not_in_progress_october() -> (
    None
):
    db = _db()
    as_of = date(2026, 10, 8)

    latest = get_latest_bill(db, "CUST001")
    statement = get_current_statement_bill(
        db,
        "CUST001",
        as_of=as_of,
    )

    assert latest is not None
    assert statement is not None
    assert latest["billing_period_start"].startswith("2026-09")
    assert statement["billing_period_start"].startswith("2026-09")

    result = get_current_bill(
        db,
        CustomerContext(customer_id="CUST001"),
    )
    assert result.data is not None
    assert result.data["period"] == "September 2026"

    db.close()


def test_cust002_statement_and_history_agree_september_unpaid() -> None:
    db = _db()
    as_of = date(2026, 10, 8)

    statement = get_current_statement_bill(
        db,
        "CUST002",
        as_of=as_of,
    )
    assert statement is not None
    assert statement["billing_period_start"].startswith("2026-09")
    assert statement["status"] == "UNPAID"

    status = get_bill_payment_status(
        db,
        CustomerContext(customer_id="CUST002"),
    )
    assert status.data is not None
    assert status.data["bill"]["period"] == "September 2026"

    payments = get_payment_history_for_customer(
        db,
        CustomerContext(customer_id="CUST002"),
        limit=2,
    )
    assert payments.status == TruthStatus.VERIFIED
    latest_payment = payments.data["payments"][0]
    assert latest_payment["bill_period"] == "September 2026"
    assert latest_payment["status"] == "FAILED"

    prior_payment = payments.data["payments"][1]
    assert prior_payment["bill_period"] == "August 2026"
    assert prior_payment["status"] == "SUCCESS"

    db.close()
