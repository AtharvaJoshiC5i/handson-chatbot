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
            s.subscription_id,
            s.customer_id,
            s.plan_id,
            s.status,
            s.activation_date AS start_date,
            s.renewal_date
        FROM subscriptions s
        JOIN plans p
          ON p.plan_id = s.plan_id
        WHERE s.customer_id = ?
          AND s.status = 'ACTIVE'
        ORDER BY
            s.renewal_date DESC,
            CASE p.plan_type
                WHEN 'FIBER' THEN 0
                ELSE 1
            END,
            s.subscription_id ASC
        LIMIT 1
        """,
        (customer_id,),
    )

    return cursor.fetchone()


def get_latest_subscription(
    db: sqlite3.Connection,
    customer_id: str,
) -> sqlite3.Row | None:
    """Return the customer's most recently activated subscription."""

    return db.execute(
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
        ORDER BY activation_date DESC, subscription_id DESC
        LIMIT 1
        """,
        (customer_id,),
    ).fetchone()


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


def list_subscriptions_for_customer(
    db: sqlite3.Connection,
    customer_id: str,
) -> list[sqlite3.Row]:
    """Return all subscriptions for one customer with plan details."""

    return db.execute(
        """
        SELECT
            s.subscription_id,
            s.customer_id,
            s.plan_id,
            s.status,
            s.activation_date AS start_date,
            s.renewal_date,
            p.plan_name,
            p.plan_type,
            p.monthly_price,
            p.data_limit_gb,
            p.is_data_unlimited,
            p.voice_limit_minutes,
            p.sms_limit
        FROM subscriptions s
        JOIN plans p
          ON p.plan_id = s.plan_id
        WHERE s.customer_id = ?
        ORDER BY
            CASE s.status
                WHEN 'ACTIVE' THEN 1
                WHEN 'SUSPENDED' THEN 2
                WHEN 'CANCELLED' THEN 3
                ELSE 4
            END,
            s.activation_date DESC,
            s.subscription_id ASC
        """,
        (customer_id,),
    ).fetchall()


def count_active_plan_types(
    db: sqlite3.Connection,
    customer_id: str,
) -> int:
    """Count distinct plan types among ACTIVE subscriptions."""

    row = db.execute(
        """
        SELECT COUNT(DISTINCT p.plan_type) AS type_count
        FROM subscriptions s
        JOIN plans p
          ON p.plan_id = s.plan_id
        WHERE s.customer_id = ?
          AND s.status = 'ACTIVE'
        """,
        (customer_id,),
    ).fetchone()

    return int(row["type_count"] if row else 0)


def get_usage_plan_for_customer(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    plan_type: str | None = None,
) -> sqlite3.Row | None:
    """
    Return subscription and plan for usage calculations.

    When plan_type is set, match that service line. Otherwise prefer
    the same ordering as historical get_customer_usage_plan.
    """

    plan_clause = ""
    params: list[object] = [customer_id]

    if plan_type is not None:
        plan_clause = " AND p.plan_type = ?"
        params.append(plan_type)

    return db.execute(
        f"""
        SELECT
            s.subscription_id,
            s.customer_id,
            s.status AS subscription_status,
            s.activation_date,
            s.renewal_date,
            p.plan_id,
            p.plan_name,
            p.plan_type,
            p.data_limit_gb,
            p.is_data_unlimited,
            p.voice_limit_minutes,
            p.sms_limit,
            p.monthly_price
        FROM subscriptions s
        JOIN plans p
          ON p.plan_id = s.plan_id
        WHERE s.customer_id = ?
        {plan_clause}
        ORDER BY
            CASE s.status
                WHEN 'ACTIVE' THEN 1
                WHEN 'SUSPENDED' THEN 2
                WHEN 'CANCELLED' THEN 3
                WHEN 'INACTIVE' THEN 4
                ELSE 5
            END,
            CASE p.plan_type
                WHEN 'FIBER' THEN 0
                ELSE 1
            END,
            s.activation_date DESC,
            s.subscription_id ASC
        LIMIT 1
        """,
        tuple(params),
    ).fetchone()


def get_customer_usage_plan(
    db: sqlite3.Connection,
    customer_id: str,
) -> sqlite3.Row | None:
    """Backward-compatible alias for usage plan resolution."""

    return get_usage_plan_for_customer(
        db,
        customer_id,
        plan_type=None,
    )
