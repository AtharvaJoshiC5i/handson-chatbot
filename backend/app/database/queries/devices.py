"""Device database queries for NexaTel."""

from __future__ import annotations

import sqlite3


def get_customer_devices(
    db: sqlite3.Connection,
    customer_id: str,
) -> list[sqlite3.Row]:
    """Return devices belonging to a customer."""

    cursor = db.execute(
        """
        SELECT
            device_id,
            customer_id,
            device_type,
            device_name AS model,
            NULL AS imei,
            status,
            purchase_date AS activated_at
        FROM devices
        WHERE customer_id = ?
        ORDER BY activated_at DESC, device_id ASC
        """,
        (customer_id,),
    )

    return cursor.fetchall()