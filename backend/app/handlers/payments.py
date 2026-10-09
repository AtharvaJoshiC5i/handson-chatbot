"""Deterministic payment intelligence and reconciliation."""

from __future__ import annotations

from calendar import month_name
from datetime import date
import sqlite3

from app.database.queries.bills import (
    get_bill_by_id_for_customer,
    get_bill_for_month,
    get_current_statement_bill,
)
from app.database.queries.payments import (
    get_latest_payment,
    get_latest_payment_by_status,
    get_payment_by_reference,
    get_payment_counts,
    get_payment_history,
    get_payments_for_bill,
    get_successful_payment_aggregate,
)
from app.models.domain import (
    CustomerContext,
    PaymentAggregateType,
    PaymentMethod,
    PaymentStatus,
    TimeRange,
)
from app.truth.result import (
    TruthResult,
    database_error_result,
    not_found_result,
    validation_error_result,
    verified_result,
)
from app.truth.sources import source_for_table


def _money(
    value: float,
) -> float:
    return round(
        float(value),
        2,
    )


def _bill_period_label(
    billing_period_start: str | None,
) -> str | None:
    if not billing_period_start:
        return None

    start = date.fromisoformat(
        billing_period_start,
    )
    return (
        f"{month_name[start.month]} "
        f"{start.year}"
    )


def _payment_dict(
    payment,
) -> dict:
    keys = payment.keys()
    bill_period = None
    if "billing_period_start" in keys:
        bill_period = _bill_period_label(
            payment["billing_period_start"],
        )

    payload = {
        "payment_id": payment[
            "payment_id"
        ],
        "bill_id": payment[
            "bill_id"
        ],
        "amount": _money(
            payment["amount"]
        ),
        "payment_date": payment[
            "payment_date"
        ],
        "payment_method": payment[
            "payment_method"
        ],
        "status": payment[
            "status"
        ],
        "transaction_reference": payment[
            "transaction_reference"
        ],
        "failure_reason": payment[
            "failure_reason"
        ],
    }

    if bill_period is not None:
        payload["bill_period"] = bill_period

    if "bill_amount" in keys and payment["bill_amount"] is not None:
        payload["bill_amount"] = _money(
            payment["bill_amount"]
        )

    return payload


def _bill_settlement_for_payment(
    db: sqlite3.Connection,
    customer_id: str,
    payment,
) -> dict[str, float | bool | str] | None:
    bill_id = payment["bill_id"]
    if not bill_id:
        return None

    bill = get_bill_by_id_for_customer(
        db,
        customer_id,
        bill_id,
    )
    if bill is None:
        return None

    attempts = get_payments_for_bill(
        db,
        customer_id,
        bill_id,
    )
    successful_paid_amount = _money(
        sum(
            float(row["amount"])
            for row in attempts
            if row["status"]
            == PaymentStatus.SUCCESS.value
        )
    )
    bill_amount = _money(bill["amount"])
    outstanding_amount = _money(
        max(
            bill_amount - successful_paid_amount,
            0.0,
        )
    )
    is_fully_paid = (
        successful_paid_amount + 0.01 >= bill_amount
    )

    return {
        "bill": _bill_dict(bill),
        "bill_amount": bill_amount,
        "successful_paid_amount": successful_paid_amount,
        "outstanding_amount": outstanding_amount,
        "is_fully_paid": is_fully_paid,
    }


def _bill_dict(
    bill,
) -> dict:
    start = date.fromisoformat(
        bill["billing_period_start"]
    )

    return {
        "bill_id": bill["bill_id"],
        "period": (
            f"{month_name[start.month]} "
            f"{start.year}"
        ),
        "billing_period_start": bill[
            "billing_period_start"
        ],
        "billing_period_end": bill[
            "billing_period_end"
        ],
        "amount": _money(
            bill["amount"]
        ),
        "due_date": bill[
            "due_date"
        ],
        "status": bill[
            "status"
        ],
    }


def _resolve_payment_period(
    *,
    time_range: TimeRange | None = None,
    month: int | None = None,
    year: int | None = None,
    month_count: int | None = None,
) -> tuple[
    str | None,
    str | None,
]:
    today = date.today()

    if month is not None:
        resolved_year = (
            year
            if year is not None
            else today.year
        )

        start = date(
            resolved_year,
            month,
            1,
        )

        if month == 12:
            next_month = date(
                resolved_year + 1,
                1,
                1,
            )
        else:
            next_month = date(
                resolved_year,
                month + 1,
                1,
            )

        end = (
            next_month
            - __import__(
                "datetime"
            ).timedelta(
                days=1
            )
        )

        return (
            start.isoformat(),
            end.isoformat(),
        )

    if time_range == TimeRange.CURRENT_MONTH:
        start = date(
            today.year,
            today.month,
            1,
        )

        return (
            start.isoformat(),
            today.isoformat(),
        )

    if time_range == TimeRange.LAST_MONTH:
        if today.month == 1:
            resolved_year = (
                today.year - 1
            )
            resolved_month = 12
        else:
            resolved_year = today.year
            resolved_month = (
                today.month - 1
            )

        return _resolve_payment_period(
            month=resolved_month,
            year=resolved_year,
        )

    if time_range == TimeRange.CURRENT_YEAR:
        return (
            date(
                today.year,
                1,
                1,
            ).isoformat(),
            today.isoformat(),
        )

    if month_count is not None:
        month_index = (
            today.year * 12
            + today.month
            - 1
            - (
                month_count
                - 1
            )
        )

        start_year = (
            month_index // 12
        )

        start_month = (
            month_index % 12
            + 1
        )

        return (
            date(
                start_year,
                start_month,
                1,
            ).isoformat(),
            today.isoformat(),
        )

    return (
        None,
        None,
    )


def _resolve_bill(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    month: int | None = None,
    year: int | None = None,
):
    if month is None:
        return get_current_statement_bill(
            db,
            customer.customer_id,
        )

    return get_bill_for_month(
        db,
        customer.customer_id,
        (
            year
            if year is not None
            else date.today().year
        ),
        month,
    )


def get_payment_status(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    """Return the customer's latest payment attempt."""

    try:
        payment = get_latest_payment(
            db,
            customer.customer_id,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve your latest payment."
            ),
        )

    if payment is None:
        return not_found_result(
            source=source_for_table(
                "payments"
            ),
            message=(
                "I don't have a payment record "
                "for your account."
            ),
        )

    payload: dict = {
        "result_type": "PAYMENT_LATEST",
        "payment": _payment_dict(payment),
    }
    settlement = _bill_settlement_for_payment(
        db,
        customer.customer_id,
        payment,
    )
    if settlement is not None:
        payload.update(settlement)

    return verified_result(
        payload,
        source=source_for_table("payments"),
    )


def get_payment_history_for_customer(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    limit: int | None = None,
    time_range: TimeRange | None = None,
    month: int | None = None,
    year: int | None = None,
    month_count: int | None = None,
) -> TruthResult[dict]:
    start_date, end_date = (
        _resolve_payment_period(
            time_range=time_range,
            month=month,
            year=year,
            month_count=month_count,
        )
    )

    if end_date is None:
        end_date = date.today().isoformat()

    try:
        payments = get_payment_history(
            db,
            customer.customer_id,
            limit=(
                limit
                if limit is not None
                else 10
            ),
            start_date=start_date,
            end_date=end_date,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve your payment history."
            ),
        )

    if not payments:
        return not_found_result(
            source=source_for_table(
                "payments"
            ),
            message=(
                "I don't have payment records "
                "for the requested period."
            ),
        )

    return verified_result(
        {
            "result_type": "PAYMENT_HISTORY",
            "payments": [
                _payment_dict(
                    payment
                )
                for payment in payments
            ],
        },
        source=source_for_table(
            "payments"
        ),
    )


def filter_payments(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    payment_status: PaymentStatus | None = None,
    payment_method: PaymentMethod | None = None,
    limit: int | None = None,
    time_range: TimeRange | None = None,
    month: int | None = None,
    year: int | None = None,
    month_count: int | None = None,
) -> TruthResult[dict]:
    start_date, end_date = (
        _resolve_payment_period(
            time_range=time_range,
            month=month,
            year=year,
            month_count=month_count,
        )
    )

    try:
        payments = get_payment_history(
            db,
            customer.customer_id,
            limit=limit,
            status=(
                payment_status.value
                if payment_status
                is not None
                else None
            ),
            payment_method=(
                payment_method.value
                if payment_method
                is not None
                else None
            ),
            start_date=start_date,
            end_date=end_date,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to filter your payment history."
            ),
        )

    if not payments:
        return not_found_result(
            source=source_for_table(
                "payments"
            ),
            message=(
                "I don't have any payment records "
                "matching those criteria."
            ),
        )

    return verified_result(
        {
            "result_type": "PAYMENT_FILTER",
            "payment_status": (
                payment_status.value
                if payment_status
                is not None
                else None
            ),
            "payment_method": (
                payment_method.value
                if payment_method
                is not None
                else None
            ),
            "payments": [
                _payment_dict(
                    payment
                )
                for payment in payments
            ],
        },
        source=source_for_table(
            "payments"
        ),
    )


def get_last_successful_payment(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    try:
        payment = (
            get_latest_payment_by_status(
                db,
                customer.customer_id,
                PaymentStatus.SUCCESS.value,
            )
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve your last "
                "successful payment."
            ),
        )

    if payment is None:
        return not_found_result(
            source=source_for_table(
                "payments"
            ),
            message=(
                "I don't have a successful payment "
                "record for your account."
            ),
        )

    return verified_result(
        {
            "result_type": (
                "PAYMENT_LAST_SUCCESSFUL"
            ),
            "payment": _payment_dict(
                payment
            ),
        },
        source=source_for_table(
            "payments"
        ),
    )


def get_last_failed_payment(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    try:
        payment = (
            get_latest_payment_by_status(
                db,
                customer.customer_id,
                PaymentStatus.FAILED.value,
            )
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve your last "
                "failed payment."
            ),
        )

    if payment is None:
        return not_found_result(
            source=source_for_table(
                "payments"
            ),
            message=(
                "I don't have a failed payment "
                "record for your account."
            ),
        )

    return verified_result(
        {
            "result_type": (
                "PAYMENT_LAST_FAILED"
            ),
            "payment": _payment_dict(
                payment
            ),
            "failure_reason": payment[
                "failure_reason"
            ],
        },
        source=source_for_table(
            "payments"
        ),
    )


def get_payment_by_transaction_reference(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    transaction_reference: str,
) -> TruthResult[dict]:
    try:
        payment = get_payment_by_reference(
            db,
            customer.customer_id,
            transaction_reference,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve that transaction."
            ),
        )

    if payment is None:
        return not_found_result(
            source=source_for_table(
                "payments"
            ),
            message=(
                "I don't have a payment transaction "
                "with that reference for your account."
            ),
        )

    return verified_result(
        {
            "result_type": (
                "PAYMENT_TRANSACTION"
            ),
            "payment": _payment_dict(
                payment
            ),
        },
        source=source_for_table(
            "payments"
        ),
    )


def reconcile_bill_payment(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    month: int | None = None,
    year: int | None = None,
) -> TruthResult[dict]:
    """
    Reconcile one customer-owned bill with every payment attempt.

    Only SUCCESS contributes to settled money.
    FAILED and PENDING never reduce outstanding_amount.
    """

    try:
        bill = _resolve_bill(
            db,
            customer,
            month=month,
            year=year,
        )

        if bill is None:
            return not_found_result(
                source=source_for_table(
                    "bills"
                ),
                message=(
                    "I don't have the requested bill."
                ),
            )

        attempts = get_payments_for_bill(
            db,
            customer.customer_id,
            bill["bill_id"],
        )

    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to reconcile the bill "
                "with its payment records."
            ),
        )

    successful = [
        payment
        for payment in attempts
        if payment["status"]
        == PaymentStatus.SUCCESS.value
    ]

    failed = [
        payment
        for payment in attempts
        if payment["status"]
        == PaymentStatus.FAILED.value
    ]

    pending = [
        payment
        for payment in attempts
        if payment["status"]
        == PaymentStatus.PENDING.value
    ]

    successful_paid_amount = _money(
        sum(
            float(payment["amount"])
            for payment in successful
        )
    )

    pending_amount = _money(
        sum(
            float(payment["amount"])
            for payment in pending
        )
    )

    failed_attempt_amount = _money(
        sum(
            float(payment["amount"])
            for payment in failed
        )
    )

    bill_amount = _money(
        bill["amount"]
    )

    outstanding_amount = _money(
        max(
            bill_amount
            - successful_paid_amount,
            0.0,
        )
    )

    is_fully_paid = (
        successful_paid_amount
        + 0.01
        >= bill_amount
    )

    stored_status = bill[
        "status"
    ]

    reconciliation_consistent = True

    if (
        stored_status == "PAID"
        and not is_fully_paid
    ):
        reconciliation_consistent = False

    if (
        stored_status
        in {
            "UNPAID",
            "OVERDUE",
        }
        and is_fully_paid
    ):
        reconciliation_consistent = False

    if (
        stored_status
        == "PARTIALLY_PAID"
        and (
            successful_paid_amount <= 0
            or is_fully_paid
        )
    ):
        reconciliation_consistent = False

    data = {
        "result_type": "PAYMENT_RECONCILIATION",
        "bill": _bill_dict(
            bill
        ),
        "payment_attempts": [
            _payment_dict(
                payment
            )
            for payment in attempts
        ],
        "attempt_count": len(
            attempts
        ),
        "successful_attempt_count": len(
            successful
        ),
        "failed_attempt_count": len(
            failed
        ),
        "pending_attempt_count": len(
            pending
        ),
        "successful_paid_amount": (
            successful_paid_amount
        ),
        "pending_amount": (
            pending_amount
        ),
        "failed_attempt_amount": (
            failed_attempt_amount
        ),
        "outstanding_amount": (
            outstanding_amount
        ),
        "is_fully_paid": (
            is_fully_paid
        ),
        "has_pending_payment": bool(
            pending
        ),
        "has_failed_attempts": bool(
            failed
        ),
        "reconciliation_consistent": (
            reconciliation_consistent
        ),
    }

    if not reconciliation_consistent:
        data[
            "result_type"
        ] = "PAYMENT_RECONCILIATION_INCONSISTENT"

    return verified_result(
        data,
        source=source_for_table(
            "payments"
        ),
    )


def get_payment_outstanding(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    month: int | None = None,
    year: int | None = None,
) -> TruthResult[dict]:
    result = reconcile_bill_payment(
        db,
        customer,
        month=month,
        year=year,
    )

    if not result.is_verified:
        return result

    data = dict(
        result.data
    )

    if (
        not data[
            "reconciliation_consistent"
        ]
    ):
        return result

    data[
        "result_type"
    ] = "PAYMENT_OUTSTANDING"

    return verified_result(
        data,
        source=source_for_table(
            "payments"
        ),
    )


def get_payment_summary(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    month: int | None = None,
    year: int | None = None,
) -> TruthResult[dict]:
    result = reconcile_bill_payment(
        db,
        customer,
        month=month,
        year=year,
    )

    if not result.is_verified:
        return result

    data = dict(
        result.data
    )

    if (
        data[
            "reconciliation_consistent"
        ]
    ):
        data[
            "result_type"
        ] = "PAYMENT_SUMMARY"

    return verified_result(
        data,
        source=source_for_table(
            "payments"
        ),
    )


def get_payment_aggregate(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    payment_aggregate_type: PaymentAggregateType,
    time_range: TimeRange | None = None,
    month: int | None = None,
    year: int | None = None,
    month_count: int | None = None,
) -> TruthResult[dict]:
    start_date, end_date = (
        _resolve_payment_period(
            time_range=time_range,
            month=month,
            year=year,
            month_count=month_count,
        )
    )

    try:
        successful = (
            get_successful_payment_aggregate(
                db,
                customer.customer_id,
                start_date=start_date,
                end_date=end_date,
            )
        )

        counts = get_payment_counts(
            db,
            customer.customer_id,
            start_date=start_date,
            end_date=end_date,
        )

    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to calculate your "
                "payment totals."
            ),
        )

    result = {
        "result_type": "PAYMENT_AGGREGATE",
        "aggregation_type": (
            payment_aggregate_type.value
        ),
        "successful_paid_amount": _money(
            successful[
                "total_amount"
            ]
        ),
        "average_successful_amount": _money(
            successful[
                "average_amount"
            ]
        ),
        "payment_attempt_count": int(
            counts[
                "attempt_count"
            ]
            or 0
        ),
        "successful_payment_count": int(
            counts[
                "successful_count"
            ]
            or 0
        ),
        "failed_payment_count": int(
            counts[
                "failed_count"
            ]
            or 0
        ),
        "pending_payment_count": int(
            counts[
                "pending_count"
            ]
            or 0
        ),
    }

    return verified_result(
        result,
        source=source_for_table(
            "payments"
        ),
    )