"""Plan database queries for NexaTel."""

from __future__ import annotations

import sqlite3


def get_plan_by_id(
    db: sqlite3.Connection,
    plan_id: str,
) -> sqlite3.Row | None:
    """Return a plan by its ID."""

    cursor = db.execute(
        """
        SELECT
            plan_id,
            plan_name AS name,
            monthly_price,
            data_limit_gb,
            is_data_unlimited,
            voice_limit_minutes,
            sms_limit,
            plan_type
        FROM plans
        WHERE plan_id = ?
        """,
        (plan_id,),
    )

    return cursor.fetchone()


def list_plans(
    db: sqlite3.Connection,
    *,
    plan_type: str | None = None,
) -> list[sqlite3.Row]:
    """Return catalog plans, optionally filtered by plan type."""

    if plan_type is None:
        return db.execute(
            """
            SELECT
                plan_id,
                plan_name,
                monthly_price,
                data_limit_gb,
                is_data_unlimited,
                voice_limit_minutes,
                sms_limit,
                plan_type
            FROM plans
            ORDER BY plan_type, monthly_price, plan_name
            """
        ).fetchall()

    return db.execute(
        """
        SELECT
            plan_id,
            plan_name,
            monthly_price,
            data_limit_gb,
            is_data_unlimited,
            voice_limit_minutes,
            sms_limit,
            plan_type
        FROM plans
        WHERE plan_type = ?
        ORDER BY monthly_price, plan_name
        """,
        (plan_type,),
    ).fetchall()
