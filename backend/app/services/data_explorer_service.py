"""Read-only paginated access to demo database tables."""

from __future__ import annotations

import sqlite3
from typing import Any

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 25

TABLE_CONFIG: dict[str, dict[str, Any]] = {
    "customers": {
        "label": "Customers",
        "filters": {
            "account_status": "account_status",
            "city": "city",
        },
        "search_columns": [
            "customer_id",
            "name",
            "email",
            "phone_number",
        ],
    },
    "plans": {
        "label": "Plans",
        "filters": {
            "plan_type": "plan_type",
        },
        "search_columns": [
            "plan_id",
            "plan_name",
        ],
    },
    "subscriptions": {
        "label": "Subscriptions",
        "filters": {
            "customer_id": "customer_id",
            "status": "status",
        },
        "search_columns": [
            "subscription_id",
            "customer_id",
            "plan_id",
        ],
    },
    "usage": {
        "label": "Usage",
        "filters": {
            "customer_id": "customer_id",
            "subscription_id": "subscription_id",
        },
        "search_columns": [
            "usage_id",
            "customer_id",
            "subscription_id",
        ],
    },
    "bills": {
        "label": "Bills",
        "filters": {
            "customer_id": "customer_id",
            "status": "status",
            "subscription_id": "subscription_id",
        },
        "search_columns": [
            "bill_id",
            "customer_id",
        ],
    },
    "bill_items": {
        "label": "Bill items",
        "filters": {
            "bill_id": "bill_id",
            "item_type": "item_type",
        },
        "search_columns": [
            "bill_item_id",
            "bill_id",
            "description",
        ],
    },
    "payments": {
        "label": "Payments",
        "filters": {
            "customer_id": "customer_id",
            "status": "status",
            "payment_method": "payment_method",
        },
        "search_columns": [
            "payment_id",
            "customer_id",
            "transaction_reference",
        ],
    },
    "support_tickets": {
        "label": "Support tickets",
        "filters": {
            "customer_id": "customer_id",
            "status": "status",
            "category": "category",
            "priority": "priority",
        },
        "search_columns": [
            "ticket_id",
            "customer_id",
            "description",
        ],
    },
    "support_ticket_updates": {
        "label": "Ticket updates",
        "filters": {
            "customer_id": "customer_id",
            "ticket_id": "ticket_id",
            "status": "status",
        },
        "search_columns": [
            "update_id",
            "ticket_id",
            "note",
        ],
    },
    "customer_payment_profiles": {
        "label": "Payment profiles",
        "filters": {
            "customer_id": "customer_id",
        },
        "search_columns": [
            "customer_id",
            "payment_method_label",
        ],
    },
    "account_credits": {
        "label": "Account credits",
        "filters": {
            "customer_id": "customer_id",
            "status": "status",
        },
        "search_columns": [
            "credit_id",
            "customer_id",
            "reason",
        ],
    },
    "devices": {
        "label": "Devices",
        "filters": {
            "customer_id": "customer_id",
            "status": "status",
        },
        "search_columns": [
            "device_id",
            "customer_id",
            "device_name",
        ],
    },
}


def list_tables(
    db: sqlite3.Connection,
) -> list[dict[str, object]]:
    tables: list[dict[str, object]] = []

    for table_name, config in TABLE_CONFIG.items():
        row = db.execute(
            f"SELECT COUNT(*) AS total FROM {table_name}",
        ).fetchone()
        total = int(row["total"]) if row is not None else 0

        tables.append(
            {
                "name": table_name,
                "label": config["label"],
                "row_count": total,
                "filters": list(config["filters"].keys()),
            },
        )

    return tables


def _table_columns(
    db: sqlite3.Connection,
    table_name: str,
) -> list[str]:
    rows = db.execute(
        f"PRAGMA table_info({table_name})",
    ).fetchall()

    return [row["name"] for row in rows]


def query_table(
    db: sqlite3.Connection,
    table_name: str,
    *,
    page: int,
    page_size: int,
    filters: dict[str, str],
    search: str | None,
) -> dict[str, object]:
    if table_name not in TABLE_CONFIG:
        raise KeyError(table_name)

    config = TABLE_CONFIG[table_name]
    columns = _table_columns(db, table_name)

    where_parts: list[str] = []
    params: list[object] = []

    for key, column in config["filters"].items():
        value = filters.get(key)

        if value is None or value == "":
            continue

        if column not in columns:
            continue

        where_parts.append(f"{column} = ?")
        params.append(value)

    if search and search.strip():
        term = f"%{search.strip()}%"
        search_cols = [
            col
            for col in config["search_columns"]
            if col in columns
        ]

        if search_cols:
            search_clause = " OR ".join(
                f"{col} LIKE ?" for col in search_cols
            )
            where_parts.append(f"({search_clause})")
            params.extend([term] * len(search_cols))

    where_sql = ""

    if where_parts:
        where_sql = " WHERE " + " AND ".join(where_parts)

    count_row = db.execute(
        f"SELECT COUNT(*) AS total FROM {table_name}{where_sql}",
        params,
    ).fetchone()
    total = int(count_row["total"]) if count_row is not None else 0

    page = max(1, page)
    page_size = min(
        MAX_PAGE_SIZE,
        max(1, page_size),
    )
    offset = (page - 1) * page_size

    data_rows = db.execute(
        f"""
        SELECT *
        FROM {table_name}
        {where_sql}
        ORDER BY rowid
        LIMIT ? OFFSET ?
        """,
        [*params, page_size, offset],
    ).fetchall()

    rows = [
        {key: row[key] for key in row.keys()}
        for row in data_rows
    ]

    filter_options: dict[str, list[str]] = {}

    for key, column in config["filters"].items():
        if column not in columns:
            continue

        option_rows = db.execute(
            f"""
            SELECT DISTINCT {column} AS value
            FROM {table_name}
            WHERE {column} IS NOT NULL
              AND {column} != ''
            ORDER BY {column}
            LIMIT 50
            """,
        ).fetchall()

        filter_options[key] = [
            str(option["value"]) for option in option_rows
        ]

    return {
        "table": table_name,
        "label": config["label"],
        "columns": columns,
        "filters": list(config["filters"].keys()),
        "filter_options": filter_options,
        "rows": rows,
        "page": page,
        "page_size": page_size,
        "total_rows": total,
        "total_pages": max(
            1,
            (total + page_size - 1) // page_size,
        )
        if total > 0
        else 1,
    }
