"""Deterministic usage database queries for NexaTel."""

from __future__ import annotations

import sqlite3


def get_usage_by_customer_and_date_range(
    db: sqlite3.Connection,
    customer_id: str,
    start_date: str,
    end_date: str,
) -> list[sqlite3.Row]:
    """
    Return raw usage records belonging only to the authenticated
    customer within an inclusive date range.
    """

    cursor = db.execute(
        """
        SELECT
            usage_id,
            customer_id,
            subscription_id,
            usage_date,
            data_used_gb,
            voice_minutes,
            sms_count
        FROM usage
        WHERE customer_id = ?
          AND usage_date >= ?
          AND usage_date <= ?
        ORDER BY usage_date ASC, usage_id ASC
        """,
        (
            customer_id,
            start_date,
            end_date,
        ),
    )

    return cursor.fetchall()


def get_usage_totals_by_date_range(
    db: sqlite3.Connection,
    customer_id: str,
    start_date: str,
    end_date: str,
) -> sqlite3.Row:
    """
    Aggregate data, voice and SMS usage for one customer.

    record_count is returned so callers can distinguish:
        no usage records
    from:
        actual recorded zero usage.
    """

    cursor = db.execute(
        """
        SELECT
            COUNT(*) AS record_count,
            COALESCE(SUM(data_used_gb), 0) AS data_used_gb,
            COALESCE(SUM(voice_minutes), 0) AS voice_minutes,
            COALESCE(SUM(sms_count), 0) AS sms_count
        FROM usage
        WHERE customer_id = ?
          AND usage_date >= ?
          AND usage_date <= ?
        """,
        (
            customer_id,
            start_date,
            end_date,
        ),
    )

    return cursor.fetchone()


def get_monthly_usage_totals(
    db: sqlite3.Connection,
    customer_id: str,
) -> list[sqlite3.Row]:
    """
    Return monthly aggregated usage totals for one customer.

    Aggregation happens in SQLite before averages, extremes,
    comparisons or trends are calculated.
    """

    cursor = db.execute(
        """
        SELECT
            substr(usage_date, 1, 7) AS period,
            COUNT(*) AS record_count,
            ROUND(SUM(data_used_gb), 4) AS data_used_gb,
            SUM(voice_minutes) AS voice_minutes,
            SUM(sms_count) AS sms_count
        FROM usage
        WHERE customer_id = ?
        GROUP BY substr(usage_date, 1, 7)
        ORDER BY period ASC
        """,
        (customer_id,),
    )

    return cursor.fetchall()


def get_customer_usage_plan(
    db: sqlite3.Connection,
    customer_id: str,
) -> sqlite3.Row | None:
    """
    Return the customer's most relevant subscription and plan.

    ACTIVE is preferred, followed by SUSPENDED, then historical
    CANCELLED/INACTIVE subscriptions.

    This lets historical usage remain queryable for cancelled
    customers without falsely treating the subscription as active.
    """

    cursor = db.execute(
        """
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
                WHEN 'INACTIVE' THEN 4
                ELSE 5
            END,
            s.activation_date DESC,
            s.subscription_id DESC
        LIMIT 1
        """,
        (customer_id,),
    )

    return cursor.fetchone()