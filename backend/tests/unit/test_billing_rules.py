"""Unit tests for NexaTel billing business logic."""

from decimal import Decimal

import pytest

from app.business.billing_rules import (
    calculate_bill_difference,
    calculate_bill_item_total,
    calculate_bill_percentage_change,
    calculate_outstanding_amount,
    determine_bill_status,
    determine_payment_status,
    money,
)
from app.models.domain import BillStatus, PaymentStatus


def test_money_normalizes_to_two_decimal_places() -> None:
    result = money("799")

    assert result == Decimal("799.00")


def test_money_rounds_using_decimal_rounding() -> None:
    result = money("799.126")

    assert result == Decimal("799.13")


def test_money_accepts_integer() -> None:
    result = money(799)

    assert result == Decimal("799.00")


def test_money_accepts_float() -> None:
    result = money(799.50)

    assert result == Decimal("799.50")


def test_calculate_bill_item_total() -> None:
    result = calculate_bill_item_total(
        [
            Decimal("799.00"),
            Decimal("301.00"),
            Decimal("43.00"),
        ]
    )

    assert result == Decimal("1143.00")


def test_calculate_bill_item_total_with_mixed_values() -> None:
    result = calculate_bill_item_total(
        [
            799,
            "301.00",
            Decimal("43.00"),
        ]
    )

    assert result == Decimal("1143.00")


def test_calculate_outstanding_amount() -> None:
    result = calculate_outstanding_amount(
        "1143.00",
        "0.00",
    )

    assert result == Decimal("1143.00")


def test_calculate_outstanding_amount_after_partial_payment() -> None:
    result = calculate_outstanding_amount(
        "1143.00",
        "500.00",
    )

    assert result == Decimal("643.00")


def test_calculate_outstanding_amount_never_returns_negative() -> None:
    result = calculate_outstanding_amount(
        "500.00",
        "700.00",
    )

    assert result == Decimal("0.00")


def test_determine_bill_status_paid() -> None:
    result = determine_bill_status(
        "799.00",
        "799.00",
    )

    assert result == BillStatus.PAID


def test_determine_bill_status_unpaid() -> None:
    result = determine_bill_status(
        "1143.00",
        "0.00",
    )

    assert result == BillStatus.UNPAID


def test_determine_bill_status_partial_payment_is_unpaid() -> None:
    result = determine_bill_status(
        "1143.00",
        "500.00",
    )

    assert result == BillStatus.UNPAID


def test_determine_payment_status_returns_verified_status() -> None:
    result = determine_payment_status(
        PaymentStatus.SUCCESS,
    )

    assert result == PaymentStatus.SUCCESS


def test_determine_payment_status_rejects_invalid_status() -> None:
    with pytest.raises(ValueError):
        determine_payment_status(
            "SUCCESS"  # type: ignore[arg-type]
        )


def test_calculate_bill_difference() -> None:
    result = calculate_bill_difference(
        "799.00",
        "1143.00",
    )

    assert result == Decimal("344.00")


def test_calculate_bill_difference_is_absolute() -> None:
    result = calculate_bill_difference(
        "1143.00",
        "799.00",
    )

    assert result == Decimal("344.00")


def test_calculate_bill_percentage_change() -> None:
    result = calculate_bill_percentage_change(
        "799.00",
        "1143.00",
    )

    assert result == Decimal("43.05")


def test_calculate_bill_percentage_change_for_decrease() -> None:
    result = calculate_bill_percentage_change(
        "1000.00",
        "750.00",
    )

    assert result == Decimal("-25.00")


def test_calculate_bill_percentage_change_from_zero() -> None:
    result = calculate_bill_percentage_change(
        "0.00",
        "799.00",
    )

    assert result is None