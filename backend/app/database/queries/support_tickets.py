"""Support-ticket database queries for NexaTel."""

from __future__ import annotations

import sqlite3


def get_support_tickets(
    db: sqlite3.Connection,
    customer_id: str,
    limit: int = 10,
) -> list[sqlite3.Row]:
    """Return support tickets belonging to a customer."""

    cursor = db.execute(
        """
        SELECT
            ticket_id,
            customer_id,
            category,
            description AS subject,
            description,
            status,
            priority,
            created_at,
            updated_at
        FROM support_tickets
        WHERE customer_id = ?
        ORDER BY created_at DESC, ticket_id DESC
        LIMIT ?
        """,
        (
            customer_id,
            limit,
        ),
    )

    return cursor.fetchall()