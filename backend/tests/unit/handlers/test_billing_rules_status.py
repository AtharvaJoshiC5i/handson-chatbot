from app.business.billing_rules import (
    determine_bill_status,
)
from app.models.domain import BillStatus


def test_paid_amount_produces_paid_status():
    assert (
        determine_bill_status(
            100,
            100,
            BillStatus.OVERDUE,
        )
        == BillStatus.PAID
    )


def test_stored_overdue_status_is_preserved_when_balance_remains():
    assert (
        determine_bill_status(
            100,
            0,
            BillStatus.OVERDUE,
        )
        == BillStatus.OVERDUE
    )


def test_stored_partial_payment_status_is_preserved():
    assert (
        determine_bill_status(
            100,
            40,
            BillStatus.PARTIALLY_PAID,
        )
        == BillStatus.PARTIALLY_PAID
    )