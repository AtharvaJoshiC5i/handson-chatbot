"""Deterministic payment queries for NexaTel."""

from __future__ import annotations

import sqlite3


PAYMENT_FIELDS = """
    payment_id,
    bill_id,
    customer_id,
    amount,
    payment_date,
    payment_method,
    status,
    transaction_reference
"""


def get_latest_payment(
    db: sqlite3.Connection,
    customer_id: str,
) -> sqlite3.Row | None:
    return db.execute(
        f"""
        SELECT {PAYMENT_FIELDS}
        FROM payments
        WHERE customer_id = ?
        ORDER BY
            payment_date DESC,
            payment_id DESC
        LIMIT 1
        """,
        (customer_id,),
    ).fetchone()


def get_latest_payment_by_status(
    db: sqlite3.Connection,
    customer_id: str,
    status: str,
) -> sqlite3.Row | None:
    return db.execute(
        f"""
        SELECT {PAYMENT_FIELDS}
        FROM payments
        WHERE customer_id = ?
          AND status = ?
        ORDER BY
            payment_date DESC,
            payment_id DESC
        LIMIT 1
        """,
        (
            customer_id,
            status,
        ),
    ).fetchone()


def get_payment_by_reference(
    db: sqlite3.Connection,
    customer_id: str,
    transaction_reference: str,
) -> sqlite3.Row | None:
    """
    Customer ID is deliberately part of this lookup.

    A valid transaction reference cannot be used to retrieve another
    customer's payment.
    """

    return db.execute(
        f"""
        SELECT {PAYMENT_FIELDS}
        FROM payments
        WHERE customer_id = ?
          AND transaction_reference = ?
        LIMIT 1
        """,
        (
            customer_id,
            transaction_reference,
        ),
    ).fetchone()


def get_payment_history(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    limit: int | None = None,
    status: str | None = None,
    payment_method: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[sqlite3.Row]:
    conditions = [
        "customer_id = ?"
    ]

    parameters: list[object] = [
        customer_id
    ]

    if status is not None:
        conditions.append(
            "status = ?"
        )
        parameters.append(
            status
        )

    if payment_method is not None:
        conditions.append(
            "payment_method = ?"
        )
        parameters.append(
            payment_method
        )

    if start_date is not None:
        conditions.append(
            "substr(payment_date, 1, 10) >= ?"
        )
        parameters.append(
            start_date
        )

    if end_date is not None:
        conditions.append(
            "substr(payment_date, 1, 10) <= ?"
        )
        parameters.append(
            end_date
        )

    sql = f"""
        SELECT {PAYMENT_FIELDS}
        FROM payments
        WHERE {" AND ".join(conditions)}
        ORDER BY
            payment_date DESC,
            payment_id DESC
    """

    if limit is not None:
        sql += "\nLIMIT ?"
        parameters.append(
            limit
        )

    return db.execute(
        sql,
        tuple(parameters),
    ).fetchall()


def get_payments_for_bill(
    db: sqlite3.Connection,
    customer_id: str,
    bill_id: str,
) -> list[sqlite3.Row]:
    """Return all attempts for a customer-owned bill."""

    return db.execute(
        f"""
        SELECT {PAYMENT_FIELDS}
        FROM payments
        WHERE customer_id = ?
          AND bill_id = ?
        ORDER BY
            payment_date ASC,
            payment_id ASC
        """,
        (
            customer_id,
            bill_id,
        ),
    ).fetchall()


def get_successful_payment_aggregate(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
) -> sqlite3.Row:
    conditions = [
        "customer_id = ?",
        "status = 'SUCCESS'",
    ]

    parameters: list[object] = [
        customer_id
    ]

    if start_date is not None:
        conditions.append(
            "substr(payment_date, 1, 10) >= ?"
        )
        parameters.append(
            start_date
        )

    if end_date is not None:
        conditions.append(
            "substr(payment_date, 1, 10) <= ?"
        )
        parameters.append(
            end_date
        )

    return db.execute(
        f"""
        SELECT
            COUNT(*) AS payment_count,
            COALESCE(
                SUM(amount),
                0
            ) AS total_amount,
            COALESCE(
                AVG(amount),
                0
            ) AS average_amount
        FROM payments
        WHERE {" AND ".join(conditions)}
        """,
        tuple(parameters),
    ).fetchone()


def get_payment_counts(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
) -> sqlite3.Row:
    conditions = [
        "customer_id = ?"
    ]

    parameters: list[object] = [
        customer_id
    ]

    if start_date is not None:
        conditions.append(
            "substr(payment_date, 1, 10) >= ?"
        )
        parameters.append(
            start_date
        )

    if end_date is not None:
        conditions.append(
            "substr(payment_date, 1, 10) <= ?"
        )
        parameters.append(
            end_date
        )

    return db.execute(
        f"""
        SELECT
            COUNT(*) AS attempt_count,

            SUM(
                CASE
                    WHEN status = 'SUCCESS'
                    THEN 1
                    ELSE 0
                END
            ) AS successful_count,

            SUM(
                CASE
                    WHEN status = 'FAILED'
                    THEN 1
                    ELSE 0
                END
            ) AS failed_count,

            SUM(
                CASE
                    WHEN status = 'PENDING'
                    THEN 1
                    ELSE 0
                END
            ) AS pending_count

        FROM payments
        WHERE {" AND ".join(conditions)}
        """,
        tuple(parameters),
    ).fetchone()