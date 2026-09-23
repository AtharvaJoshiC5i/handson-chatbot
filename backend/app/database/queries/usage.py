"""Usage database queries for NexaTel."""

from __future__ import annotations

import sqlite3


def get_usage_by_customer_and_date_range(
    db: sqlite3.Connection,
    customer_id: str,
    start_date: str,
    end_date: str,
) -> list[sqlite3.Row]:
    """Return usage records belonging to a customer within a date range."""

    cursor = db.execute(
        """
                SELECT
                        usage_id,
                        customer_id,
                        usage_date,
                        'DATA' AS usage_type,
                        data_used_gb AS amount,
                        'GB' AS unit
                FROM usage
                WHERE customer_id = ?
                    AND usage_date >= ?
                    AND usage_date <= ?

                UNION ALL

                SELECT
                        usage_id,
                        customer_id,
                        usage_date,
                        'VOICE' AS usage_type,
                        voice_minutes AS amount,
                        'MINUTES' AS unit
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
                        customer_id,
                        start_date,
                        end_date,
        ),
    )

    return cursor.fetchall()