"""Deterministic billing queries for NexaTel."""

from __future__ import annotations

import sqlite3


def get_latest_bill(
    db: sqlite3.Connection,
    customer_id: str,
) -> sqlite3.Row | None:
    """Return the customer's latest available bill."""

    return db.execute(
        """
        SELECT
            bill_id,
            customer_id,
            billing_period_start,
            billing_period_end,
            amount,
            due_date,
            status
        FROM bills
        WHERE customer_id = ?
        ORDER BY
            billing_period_end DESC,
            bill_id DESC
        LIMIT 1
        """,
        (customer_id,),
    ).fetchone()


def get_bill_by_id_for_customer(
    db: sqlite3.Connection,
    customer_id: str,
    bill_id: str,
) -> sqlite3.Row | None:
    """Return a bill only if it belongs to the customer."""

    return db.execute(
        """
        SELECT
            bill_id,
            customer_id,
            billing_period_start,
            billing_period_end,
            amount,
            due_date,
            status
        FROM bills
        WHERE customer_id = ?
          AND bill_id = ?
        LIMIT 1
        """,
        (
            customer_id,
            bill_id,
        ),
    ).fetchone()


def get_bill_for_month(
    db: sqlite3.Connection,
    customer_id: str,
    year: int,
    month: int,
) -> sqlite3.Row | None:
    """Return the customer's bill covering the requested month."""

    period = (
        f"{year}-{month:02d}"
    )

    return db.execute(
        """
        SELECT
            bill_id,
            customer_id,
            billing_period_start,
            billing_period_end,
            amount,
            due_date,
            status
        FROM bills
        WHERE customer_id = ?
          AND substr(
                billing_period_start,
                1,
                7
              ) = ?
        ORDER BY billing_period_end DESC
        LIMIT 1
        """,
        (
            customer_id,
            period,
        ),
    ).fetchone()


def get_previous_bill(
    db: sqlite3.Connection,
    customer_id: str,
    before_period_start: str,
) -> sqlite3.Row | None:
    """Return the bill immediately before a supplied bill period."""

    return db.execute(
        """
        SELECT
            bill_id,
            customer_id,
            billing_period_start,
            billing_period_end,
            amount,
            due_date,
            status
        FROM bills
        WHERE customer_id = ?
          AND billing_period_start < ?
        ORDER BY
            billing_period_start DESC,
            bill_id DESC
        LIMIT 1
        """,
        (
            customer_id,
            before_period_start,
        ),
    ).fetchone()


def get_bill_history(
    db: sqlite3.Connection,
    customer_id: str,
    limit: int | None = None,
) -> list[sqlite3.Row]:
    """Return bill history newest first."""

    sql = """
        SELECT
            bill_id,
            customer_id,
            billing_period_start,
            billing_period_end,
            amount,
            due_date,
            status
        FROM bills
        WHERE customer_id = ?
        ORDER BY
            billing_period_start DESC,
            bill_id DESC
    """

    parameters: list[object] = [
        customer_id
    ]

    if limit is not None:
        sql += "\nLIMIT ?"
        parameters.append(limit)

    return db.execute(
        sql,
        tuple(parameters),
    ).fetchall()


def get_bills_for_date_range(
    db: sqlite3.Connection,
    customer_id: str,
    start_date: str,
    end_date: str,
) -> list[sqlite3.Row]:
    """Return bills whose period starts within a date range."""

    return db.execute(
        """
        SELECT
            bill_id,
            customer_id,
            billing_period_start,
            billing_period_end,
            amount,
            due_date,
            status
        FROM bills
        WHERE customer_id = ?
          AND billing_period_start >= ?
          AND billing_period_start <= ?
        ORDER BY billing_period_start ASC
        """,
        (
            customer_id,
            start_date,
            end_date,
        ),
    ).fetchall()


def get_bill_items(
    db: sqlite3.Connection,
    bill_id: str,
) -> list[sqlite3.Row]:
    """Return all itemized charges belonging to a bill."""

    return db.execute(
        """
        SELECT
            bill_item_id,
            bill_id,
            description,
            amount,
            item_type
        FROM bill_items
        WHERE bill_id = ?
        ORDER BY bill_item_id ASC
        """,
        (bill_id,),
    ).fetchall()


def get_filtered_bills(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    status: str | None = None,
    minimum_amount: float | None = None,
    limit: int | None = None,
    sort_order: str = "NEWEST",
) -> list[sqlite3.Row]:
    """Return customer-owned bills using controlled billing filters."""

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

    if minimum_amount is not None:
        conditions.append(
            "amount >= ?"
        )

        parameters.append(
            minimum_amount
        )

    order_by = {
        "NEWEST": (
            "billing_period_start DESC, "
            "bill_id DESC"
        ),
        "OLDEST": (
            "billing_period_start ASC, "
            "bill_id ASC"
        ),
        "AMOUNT_HIGH_TO_LOW": (
            "amount DESC, "
            "billing_period_start DESC"
        ),
        "AMOUNT_LOW_TO_HIGH": (
            "amount ASC, "
            "billing_period_start DESC"
        ),
    }.get(
        sort_order,
        "billing_period_start DESC, bill_id DESC",
    )

    sql = f"""
        SELECT
            bill_id,
            customer_id,
            billing_period_start,
            billing_period_end,
            amount,
            due_date,
            status
        FROM bills
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


def get_bill_item_total(
    db: sqlite3.Connection,
    bill_id: str,
) -> sqlite3.Row:
    """Return bill-item count and deterministic item total."""

    return db.execute(
        """
        SELECT
            COUNT(*) AS item_count,
            COALESCE(
                SUM(amount),
                0
            ) AS item_total
        FROM bill_items
        WHERE bill_id = ?
        """,
        (bill_id,),
    ).fetchone()