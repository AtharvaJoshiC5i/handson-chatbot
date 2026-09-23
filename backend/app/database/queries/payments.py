"""Payment database queries for NexaTel."""

from __future__ import annotations

import sqlite3


def get_payment_status_for_customer(
    db: sqlite3.Connection,
    customer_id: str,
) -> sqlite3.Row | None:
    """Return the most recent payment for a customer."""

    cursor = db.execute(
        """
        SELECT
            payment_id,
            customer_id,
            bill_id,
            amount,
            payment_date,
            payment_method,
            status,
            transaction_reference AS reference
        FROM payments
        WHERE customer_id = ?
        ORDER BY payment_date DESC, payment_id DESC
        LIMIT 1
        """,
        (customer_id,),
    )

    return cursor.fetchone()


def get_payment_history(
    db: sqlite3.Connection,
    customer_id: str,
    limit: int = 10,
) -> list[sqlite3.Row]:
    """Return payment history for a customer."""

    cursor = db.execute(
        """
        SELECT
            payment_id,
            customer_id,
            bill_id,
            amount,
            payment_date,
            payment_method,
            status,
            transaction_reference AS reference
        FROM payments
        WHERE customer_id = ?
        ORDER BY payment_date DESC, payment_id DESC
        LIMIT ?
        """,
        (
            customer_id,
            limit,
        ),
    )

    return cursor.fetchall()