"""Subscription database queries for NexaTel."""

from __future__ import annotations

import sqlite3


def get_current_subscription(
    db: sqlite3.Connection,
    customer_id: str,
) -> sqlite3.Row | None:
    """Return the customer's current active subscription."""

    cursor = db.execute(
        """
        SELECT
            subscription_id,
            customer_id,
            plan_id,
            status,
            activation_date AS start_date,
            renewal_date
        FROM subscriptions
        WHERE customer_id = ?
          AND status = 'ACTIVE'
        ORDER BY renewal_date DESC, subscription_id DESC
        LIMIT 1
        """,
        (customer_id,),
    )

    return cursor.fetchone()


def get_subscription_by_id(
    db: sqlite3.Connection,
    subscription_id: str,
    customer_id: str,
) -> sqlite3.Row | None:
    """Return a subscription only when it belongs to the customer."""

    cursor = db.execute(
        """
        SELECT
            subscription_id,
            customer_id,
            plan_id,
            status,
            activation_date AS start_date,
            renewal_date
        FROM subscriptions
        WHERE subscription_id = ?
          AND customer_id = ?
        """,
        (subscription_id, customer_id),
    )

    return cursor.fetchone()