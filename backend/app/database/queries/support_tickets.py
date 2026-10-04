"""Deterministic support-ticket queries for NexaTel."""

from __future__ import annotations

import sqlite3


SUPPORT_TICKET_FIELDS = """
    ticket_id,
    customer_id,
    category,
    description,
    status,
    priority,
    created_at,
    updated_at,
    related_bill_id,
    related_payment_id
"""


def get_latest_support_ticket(
    db: sqlite3.Connection,
    customer_id: str,
) -> sqlite3.Row | None:
    """Return the customer's most recently created ticket."""

    return db.execute(
        f"""
        SELECT {SUPPORT_TICKET_FIELDS}
        FROM support_tickets
        WHERE customer_id = ?
        ORDER BY
            created_at DESC,
            ticket_id DESC
        LIMIT 1
        """,
        (customer_id,),
    ).fetchone()


def get_support_ticket_by_id(
    db: sqlite3.Connection,
    customer_id: str,
    ticket_id: str,
) -> sqlite3.Row | None:
    """
    Return a ticket only when it belongs to the trusted customer.

    A ticket ID by itself is never sufficient authorization.
    """

    return db.execute(
        f"""
        SELECT {SUPPORT_TICKET_FIELDS}
        FROM support_tickets
        WHERE customer_id = ?
          AND ticket_id = ?
        LIMIT 1
        """,
        (
            customer_id,
            ticket_id,
        ),
    ).fetchone()


def get_support_tickets(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    statuses: tuple[str, ...] | None = None,
    priorities: tuple[str, ...] | None = None,
    categories: tuple[str, ...] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = None,
    sort_order: str = "NEWEST",
) -> list[sqlite3.Row]:
    """Return customer-owned support tickets using controlled filters."""

    conditions = [
        "customer_id = ?"
    ]

    parameters: list[object] = [
        customer_id
    ]

    if statuses:
        placeholders = ", ".join(
            "?"
            for _ in statuses
        )

        conditions.append(
            f"status IN ({placeholders})"
        )

        parameters.extend(
            statuses
        )

    if priorities:
        placeholders = ", ".join(
            "?"
            for _ in priorities
        )

        conditions.append(
            f"priority IN ({placeholders})"
        )

        parameters.extend(
            priorities
        )

    if categories:
        placeholders = ", ".join(
            "?"
            for _ in categories
        )

        conditions.append(
            f"category IN ({placeholders})"
        )

        parameters.extend(
            categories
        )

    if start_date is not None:
        conditions.append(
            "substr(created_at, 1, 10) >= ?"
        )

        parameters.append(
            start_date
        )

    if end_date is not None:
        conditions.append(
            "substr(created_at, 1, 10) <= ?"
        )

        parameters.append(
            end_date
        )

    order_by = (
        "created_at ASC, ticket_id ASC"
        if sort_order == "OLDEST"
        else "created_at DESC, ticket_id DESC"
    )

    sql = f"""
        SELECT {SUPPORT_TICKET_FIELDS}
        FROM support_tickets
        WHERE {" AND ".join(conditions)}
        ORDER BY {order_by}
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


def get_support_ticket_counts(
    db: sqlite3.Connection,
    customer_id: str,
) -> sqlite3.Row:
    """Return deterministic support counts for one customer."""

    return db.execute(
        """
        SELECT
            COUNT(*) AS total_count,

            SUM(
                CASE
                    WHEN status IN (
                        'OPEN',
                        'IN_PROGRESS'
                    )
                    THEN 1
                    ELSE 0
                END
            ) AS unresolved_count,

            SUM(
                CASE
                    WHEN status IN (
                        'RESOLVED',
                        'CLOSED'
                    )
                    THEN 1
                    ELSE 0
                END
            ) AS resolved_count,

            SUM(
                CASE
                    WHEN priority = 'HIGH'
                    THEN 1
                    ELSE 0
                END
            ) AS high_count,

            SUM(
                CASE
                    WHEN priority = 'CRITICAL'
                    THEN 1
                    ELSE 0
                END
            ) AS critical_count

        FROM support_tickets
        WHERE customer_id = ?
        """,
        (customer_id,),
    ).fetchone()


def get_support_category_counts(
    db: sqlite3.Connection,
    customer_id: str,
) -> list[sqlite3.Row]:
    """Return category counts ordered by frequency."""

    return db.execute(
        """
        SELECT
            category,
            COUNT(*) AS ticket_count
        FROM support_tickets
        WHERE customer_id = ?
        GROUP BY category
        ORDER BY
            ticket_count DESC,
            category ASC
        """,
        (customer_id,),
    ).fetchall()


def get_support_ticket_updates(
    db: sqlite3.Connection,
    customer_id: str,
    ticket_id: str,
) -> list[sqlite3.Row]:
    """Return structured update history for one customer-owned ticket."""

    return db.execute(
        """
        SELECT
            update_id,
            ticket_id,
            customer_id,
            updated_at,
            status,
            note
        FROM support_ticket_updates
        WHERE customer_id = ?
          AND ticket_id = ?
        ORDER BY updated_at ASC, update_id ASC
        """,
        (
            customer_id,
            ticket_id,
        ),
    ).fetchall()


def list_all_ticket_updates_for_customer(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    ticket_id: str | None = None,
    limit: int = 25,
) -> list[sqlite3.Row]:
    """Return ticket update rows for one customer."""

    clauses = ["customer_id = ?"]
    params: list[object] = [customer_id]

    if ticket_id is not None:
        clauses.append("ticket_id = ?")
        params.append(ticket_id)

    params.append(limit)

    return db.execute(
        f"""
        SELECT
            update_id,
            ticket_id,
            customer_id,
            updated_at,
            status,
            note
        FROM support_ticket_updates
        WHERE {" AND ".join(clauses)}
        ORDER BY updated_at DESC, update_id DESC
        LIMIT ?
        """,
        params,
    ).fetchall()