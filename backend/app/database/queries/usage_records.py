"""Daily usage record queries."""

from __future__ import annotations

import sqlite3


def list_usage_records(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    subscription_id: str | None = None,
    limit: int = 25,
) -> list[sqlite3.Row]:
    """Return daily usage rows for one customer, newest first."""

    clauses = ["u.customer_id = ?"]
    params: list[object] = [customer_id]

    if subscription_id is not None:
        clauses.append("u.subscription_id = ?")
        params.append(subscription_id)

    params.append(limit)

    return db.execute(
        f"""
        SELECT
            u.usage_id,
            u.customer_id,
            u.subscription_id,
            u.usage_date,
            u.data_used_gb,
            u.voice_minutes,
            u.sms_count
        FROM usage u
        WHERE {" AND ".join(clauses)}
        ORDER BY u.usage_date DESC, u.usage_id DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
