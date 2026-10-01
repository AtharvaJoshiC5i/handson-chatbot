"""Deterministic device queries for NexaTel."""

from __future__ import annotations

import sqlite3


DEVICE_FIELDS = """
    device_id,
    customer_id,
    device_name,
    device_type,
    purchase_date,
    status
"""


def get_device_by_id(
    db: sqlite3.Connection,
    customer_id: str,
    device_id: str,
) -> sqlite3.Row | None:
    """Return a device only when it belongs to the customer."""

    return db.execute(
        f"""
        SELECT {DEVICE_FIELDS}
        FROM devices
        WHERE customer_id = ?
          AND device_id = ?
        LIMIT 1
        """,
        (
            customer_id,
            device_id,
        ),
    ).fetchone()


def get_devices(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    statuses: tuple[str, ...] | None = None,
    device_types: tuple[str, ...] | None = None,
    sort_order: str = "NEWEST",
    limit: int | None = None,
) -> list[sqlite3.Row]:
    """Return customer-owned devices using controlled filters."""

    conditions = [
        "customer_id = ?"
    ]

    parameters: list[object] = [
        customer_id
    ]

    if statuses:
        placeholders = ", ".join(
            "?"
            for _ in statuses
        )

        conditions.append(
            f"status IN ({placeholders})"
        )

        parameters.extend(
            statuses
        )

    if device_types:
        placeholders = ", ".join(
            "?"
            for _ in device_types
        )

        conditions.append(
            f"device_type IN ({placeholders})"
        )

        parameters.extend(
            device_types
        )

    order_by = {
        "NEWEST": (
            "purchase_date DESC, device_id DESC"
        ),
        "OLDEST": (
            "purchase_date ASC, device_id ASC"
        ),
    }.get(
        sort_order,
        "purchase_date DESC, device_id DESC",
    )

    sql = f"""
        SELECT {DEVICE_FIELDS}
        FROM devices
        WHERE {" AND ".join(conditions)}
        ORDER BY {order_by}
    """

    if limit is not None:
        sql += "\nLIMIT ?"

        parameters.append(
            limit
        )

    return db.execute(
        sql,
        tuple(parameters),
    ).fetchall()


def get_newest_device(
    db: sqlite3.Connection,
    customer_id: str,
) -> sqlite3.Row | None:
    """Return the newest recorded device by purchase date."""

    return db.execute(
        f"""
        SELECT {DEVICE_FIELDS}
        FROM devices
        WHERE customer_id = ?
        ORDER BY
            purchase_date DESC,
            device_id DESC
        LIMIT 1
        """,
        (customer_id,),
    ).fetchone()


def get_oldest_device(
    db: sqlite3.Connection,
    customer_id: str,
) -> sqlite3.Row | None:
    """Return the oldest recorded device by purchase date."""

    return db.execute(
        f"""
        SELECT {DEVICE_FIELDS}
        FROM devices
        WHERE customer_id = ?
        ORDER BY
            purchase_date ASC,
            device_id ASC
        LIMIT 1
        """,
        (customer_id,),
    ).fetchone()


def get_device_counts(
    db: sqlite3.Connection,
    customer_id: str,
) -> sqlite3.Row:
    """Return deterministic device-status counts."""

    return db.execute(
        """
        SELECT
            COUNT(*) AS total_count,

            SUM(
                CASE
                    WHEN status = 'ACTIVE'
                    THEN 1
                    ELSE 0
                END
            ) AS active_count,

            SUM(
                CASE
                    WHEN status = 'INACTIVE'
                    THEN 1
                    ELSE 0
                END
            ) AS inactive_count,

            SUM(
                CASE
                    WHEN status = 'REPLACED'
                    THEN 1
                    ELSE 0
                END
            ) AS replaced_count,

            SUM(
                CASE
                    WHEN status = 'LOST'
                    THEN 1
                    ELSE 0
                END
            ) AS lost_count

        FROM devices
        WHERE customer_id = ?
        """,
        (customer_id,),
    ).fetchone()


def get_device_type_counts(
    db: sqlite3.Connection,
    customer_id: str,
) -> list[sqlite3.Row]:
    """Return counts grouped by structured device type."""

    return db.execute(
        """
        SELECT
            device_type,
            COUNT(*) AS device_count
        FROM devices
        WHERE customer_id = ?
        GROUP BY device_type
        ORDER BY
            device_count DESC,
            device_type ASC
        """,
        (customer_id,),
    ).fetchall()