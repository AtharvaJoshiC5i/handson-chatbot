"""Plan database queries for NexaTel."""

from __future__ import annotations

import sqlite3


def get_plan_by_id(
    db: sqlite3.Connection,
    plan_id: str,
) -> sqlite3.Row | None:
    """Return a plan by its ID using only fields present in the schema."""

    cursor = db.execute(
        """
        SELECT
            plan_id,
            plan_name AS name,
            monthly_price,
            data_limit_gb,
            voice_limit_minutes,
            sms_limit,
            plan_type
        FROM plans
        WHERE plan_id = ?
        """,
        (plan_id,),
    )

    return cursor.fetchone()