"""Customer database queries for NexaTel."""

from __future__ import annotations

import sqlite3


def get_customer(
    db: sqlite3.Connection,
    customer_id: str,
) -> sqlite3.Row | None:
    """Return one customer by customer ID."""

    cursor = db.execute(
        """
        SELECT
            customer_id,
            name,
            email,
            phone_number AS phone,
            account_status,
            registration_date AS created_at
        FROM customers
        WHERE customer_id = ?
        """,
        (customer_id,),
    )

    return cursor.fetchone()