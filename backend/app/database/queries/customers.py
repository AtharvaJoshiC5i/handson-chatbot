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
            city,
            service_address_line,
            service_state,
            service_postal_code,
            account_status,
            registration_date AS created_at
        FROM customers
        WHERE customer_id = ?
        """,
        (customer_id,),
    )

    return cursor.fetchone()


def list_demo_customers(
    db: sqlite3.Connection,
) -> list[sqlite3.Row]:
    """Return demo customers for the account switcher."""

    cursor = db.execute(
        """
        SELECT
            customer_id,
            name,
            phone_number AS phone
        FROM customers
        ORDER BY customer_id ASC
        """,
    )

    return cursor.fetchall()
