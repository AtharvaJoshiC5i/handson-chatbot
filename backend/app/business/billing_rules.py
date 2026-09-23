"""Deterministic billing business rules for NexaTel."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from app.models.domain import BillStatus, PaymentStatus


MONEY_QUANTIZER = Decimal("0.01")


def money(value: Decimal | float | int | str) -> Decimal:
    """Normalize a monetary value to two decimal places."""

    return Decimal(str(value)).quantize(
        MONEY_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )


def calculate_bill_item_total(
    item_amounts: Iterable[Decimal | float | int | str],
) -> Decimal:
    """Calculate a bill total from verified bill-item amounts."""

    total = Decimal("0.00")

    for amount in item_amounts:
        total += money(amount)

    return money(total)


def calculate_outstanding_amount(
    total_amount: Decimal | float | int | str,
    paid_amount: Decimal | float | int | str,
) -> Decimal:
    """Calculate the remaining amount owed on a bill."""

    total = money(total_amount)
    paid = money(paid_amount)

    outstanding = total - paid

    if outstanding < Decimal("0.00"):
        outstanding = Decimal("0.00")

    return money(outstanding)


def determine_bill_status(
    total_amount: Decimal | float | int | str,
    paid_amount: Decimal | float | int | str,
    stored_status: BillStatus | str | None = None,
) -> BillStatus:
    """
    Determine bill status without discarding authoritative bill state.

    A fully paid bill is always PAID.

    If the database explicitly marks an unpaid bill as OVERDUE or
    PARTIALLY_PAID, that state is preserved.

    Otherwise the result falls back to UNPAID.
    """

    total = money(total_amount)
    paid = money(paid_amount)

    if paid >= total:
        return BillStatus.PAID

    if isinstance(stored_status, str):
        try:
            stored_status = BillStatus(stored_status)
        except ValueError:
            stored_status = None

    if stored_status in {
        BillStatus.OVERDUE,
        BillStatus.PARTIALLY_PAID,
    }:
        return stored_status

    return BillStatus.UNPAID


def determine_payment_status(
    payment_status: PaymentStatus,
) -> PaymentStatus:
    """Return the verified payment status."""

    if not isinstance(payment_status, PaymentStatus):
        raise ValueError("Invalid payment status.")

    return payment_status


def calculate_bill_difference(
    first_bill_total: Decimal | float | int | str,
    second_bill_total: Decimal | float | int | str,
) -> Decimal:
    """Calculate the absolute difference between two verified bills."""

    first = money(first_bill_total)
    second = money(second_bill_total)

    return money(abs(first - second))


def calculate_bill_percentage_change(
    previous_total: Decimal | float | int | str,
    current_total: Decimal | float | int | str,
) -> Decimal | None:
    """Calculate percentage change between two verified bill totals."""

    previous = money(previous_total)
    current = money(current_total)

    if previous == Decimal("0.00"):
        return None

    percentage = (
        (current - previous) / previous
    ) * Decimal("100")

    return percentage.quantize(
        MONEY_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )