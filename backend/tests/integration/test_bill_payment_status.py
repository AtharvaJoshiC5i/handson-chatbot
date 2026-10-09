"""Bill and payment reconciliation presentation for demo personas."""

from __future__ import annotations

import sqlite3

from app.database.seed import seed_database
from app.handlers.cross_domain import get_bill_payment_status
from app.models.domain import CustomerContext, TruthStatus
from app.services.presentation_service import (
    PresentationService,
    _bill_payment_outstanding_secondary,
    _bill_payment_paid_secondary,
)


def _db() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    seed_database(connection, reset=True)
    return connection


def test_cust002_bill_payment_links_failed_attempt_to_outstanding() -> None:
    db = _db()
    result = get_bill_payment_status(
        db,
        CustomerContext(customer_id="CUST002"),
    )
    assert result.status == TruthStatus.VERIFIED
    data = result.data or {}
    bill = data["bill"]
    payment = data["payment"]

    assert float(bill["amount"]) == 1143.0
    assert float(payment["successful_paid_amount"]) == 0.0
    assert float(payment["outstanding_amount"]) == 1143.0
    assert payment["failed_attempt_count"] == 1
    assert float(payment.get("failed_attempt_amount", 0)) == 1143.0

    paid_secondary = _bill_payment_paid_secondary(payment)
    outstanding_secondary = _bill_payment_outstanding_secondary(
        payment,
        bill,
    )

    assert "failed" in paid_secondary.lower()
    assert "pending" not in outstanding_secondary.lower() or "clearance" in outstanding_secondary.lower()
    assert "failed" in outstanding_secondary.lower()

    presentation = PresentationService().build(result)
    assert presentation is not None
    assert presentation.type == "summary"
    outstanding_section = next(
        section
        for section in presentation.sections
        if section.label == "Outstanding"
    )
    assert "₹0 pending" not in outstanding_section.secondary.lower()

    db.close()
