"""Deterministic usage database queries for NexaTel."""

from __future__ import annotations

import sqlite3

from app.database.queries.subscriptions import (
    get_customer_usage_plan,
)


def get_usage_by_customer_and_date_range(
    db: sqlite3.Connection,
    customer_id: str,
    start_date: str,
    end_date: str,
    *,
    subscription_id: str | None = None,
) -> list[sqlite3.Row]:
    """Return raw usage records for one customer in a date range."""

    subscription_clause = ""
    params: list[object] = [
        customer_id,
        start_date,
        end_date,
    ]

    if subscription_id is not None:
        subscription_clause = " AND subscription_id = ?"
        params.append(subscription_id)

    cursor = db.execute(
        f"""
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
        {subscription_clause}
        ORDER BY usage_date ASC, usage_id ASC
        """,
        tuple(params),
    )

    return cursor.fetchall()


def get_usage_totals_by_date_range(
    db: sqlite3.Connection,
    customer_id: str,
    start_date: str,
    end_date: str,
    *,
    subscription_id: str | None = None,
) -> sqlite3.Row:
    """Aggregate usage for one customer in an inclusive date range."""

    subscription_clause = ""
    params: list[object] = [
        customer_id,
        start_date,
        end_date,
    ]

    if subscription_id is not None:
        subscription_clause = " AND subscription_id = ?"
        params.append(subscription_id)

    cursor = db.execute(
        f"""
        SELECT
            COUNT(*) AS record_count,
            COALESCE(SUM(data_used_gb), 0) AS data_used_gb,
            COALESCE(SUM(voice_minutes), 0) AS voice_minutes,
            COALESCE(SUM(sms_count), 0) AS sms_count
        FROM usage
        WHERE customer_id = ?
          AND usage_date >= ?
          AND usage_date <= ?
        {subscription_clause}
        """,
        tuple(params),
    )

    return cursor.fetchone()


def get_monthly_usage_totals(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    subscription_id: str | None = None,
) -> list[sqlite3.Row]:
    """Return monthly aggregated usage totals for one customer."""

    subscription_clause = ""
    params: list[object] = [customer_id]

    if subscription_id is not None:
        subscription_clause = " AND subscription_id = ?"
        params.append(subscription_id)

    cursor = db.execute(
        f"""
        SELECT
            substr(usage_date, 1, 7) AS period,
            COUNT(*) AS record_count,
            ROUND(SUM(data_used_gb), 4) AS data_used_gb,
            SUM(voice_minutes) AS voice_minutes,
            SUM(sms_count) AS sms_count
        FROM usage
        WHERE customer_id = ?
        {subscription_clause}
        GROUP BY substr(usage_date, 1, 7)
        ORDER BY period ASC
        """,
        tuple(params),
    )

    return cursor.fetchall()


__all__ = [
    "get_customer_usage_plan",
    "get_usage_by_customer_and_date_range",
    "get_usage_totals_by_date_range",
    "get_monthly_usage_totals",
]
