"""Billing database queries for NexaTel."""

from __future__ import annotations

import sqlite3


def get_current_bill(
    db: sqlite3.Connection,
    customer_id: str,
) -> sqlite3.Row | None:
    """Return the most recent bill for the authenticated customer."""

    cursor = db.execute(
        """
        SELECT
            bill_id,
            customer_id,
            billing_period_start,
            billing_period_end,
            due_date,
            amount AS total_amount,
            COALESCE(
                (
                    SELECT SUM(p.amount)
                    FROM payments AS p
                    WHERE p.bill_id = bills.bill_id
                      AND p.customer_id = bills.customer_id
                      AND p.status = 'SUCCESS'
                ),
                0
            ) AS paid_amount,
            status
        FROM bills
        WHERE customer_id = ?
        ORDER BY billing_period_end DESC, bill_id DESC
        LIMIT 1
        """,
        (customer_id,),
    )

    return cursor.fetchone()


def get_bill_by_id(
    db: sqlite3.Connection,
    bill_id: str,
    customer_id: str,
) -> sqlite3.Row | None:
    """Return a bill only when it belongs to the authenticated customer."""

    cursor = db.execute(
        """
        SELECT
            bill_id,
            customer_id,
            billing_period_start,
            billing_period_end,
            due_date,
            amount AS total_amount,
            COALESCE(
                (
                    SELECT SUM(p.amount)
                    FROM payments AS p
                    WHERE p.bill_id = bills.bill_id
                      AND p.customer_id = bills.customer_id
                      AND p.status = 'SUCCESS'
                ),
                0
            ) AS paid_amount,
            status
        FROM bills
        WHERE bill_id = ?
          AND customer_id = ?
        """,
        (
            bill_id,
            customer_id,
        ),
    )

    return cursor.fetchone()


def get_bill_history(
    db: sqlite3.Connection,
    customer_id: str,
    limit: int = 10,
) -> list[sqlite3.Row]:
    """Return bill history for the authenticated customer."""

    cursor = db.execute(
        """
        SELECT
            bill_id,
            customer_id,
            billing_period_start,
            billing_period_end,
            due_date,
            amount AS total_amount,
            COALESCE(
                (
                    SELECT SUM(p.amount)
                    FROM payments AS p
                    WHERE p.bill_id = bills.bill_id
                      AND p.customer_id = bills.customer_id
                      AND p.status = 'SUCCESS'
                ),
                0
            ) AS paid_amount,
            status
        FROM bills
        WHERE customer_id = ?
        ORDER BY billing_period_end DESC, bill_id DESC
        LIMIT ?
        """,
        (
            customer_id,
            limit,
        ),
    )

    return cursor.fetchall()


def get_bill_items(
    db: sqlite3.Connection,
    bill_id: str,
    customer_id: str,
) -> list[sqlite3.Row]:
    """Return bill items only for a customer-owned bill."""

    cursor = db.execute(
        """
        SELECT
            bi.bill_item_id,
            bi.bill_id,
            bi.item_type,
            bi.description,
            bi.amount
        FROM bill_items AS bi
        INNER JOIN bills AS b
            ON b.bill_id = bi.bill_id
        WHERE bi.bill_id = ?
          AND b.customer_id = ?
        ORDER BY bi.bill_item_id ASC
        """,
        (
            bill_id,
            customer_id,
        ),
    )

    return cursor.fetchall()