"""Print the complete NexaTel SQLite database in a readable view."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Sequence

# Allow `python scripts/view_database.py` from the backend directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.connection import create_connection, get_database_path


def get_table_names(connection: sqlite3.Connection) -> list[str]:
    """Return application tables in creation order."""

    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return [row[0] for row in rows]


def quote_identifier(identifier: str) -> str:
    """Quote a SQLite identifier after it came from sqlite_master."""

    return '"' + identifier.replace('"', '""') + '"'


def print_table(connection: sqlite3.Connection, table_name: str) -> None:
    """Print schema details and every row for one table."""

    columns = connection.execute(
        f"PRAGMA table_info({quote_identifier(table_name)})"
    ).fetchall()
    rows = connection.execute(
        f"SELECT * FROM {quote_identifier(table_name)}"
    ).fetchall()

    print(f"\n{'=' * 88}")
    print(f"TABLE: {table_name} ({len(rows)} rows)")
    print(f"{'=' * 88}")
    print("COLUMNS")
    for column in columns:
        nullable = "NOT NULL" if column[3] else "NULL"
        primary_key = " PRIMARY KEY" if column[5] else ""
        print(f"  {column[1]}: {column[2] or 'ANY'} {nullable}{primary_key}")

    print("ROWS")
    if not rows:
        print("  <empty>")
        return

    for row_number, row in enumerate(rows, start=1):
        values = {column[1]: row[column[1]] for column in columns}
        print(f"  {row_number}. {json.dumps(values, default=str, sort_keys=False)}")


def main(arguments: Sequence[str] | None = None) -> None:
    """Display all tables, or only the tables requested with --table."""

    parser = argparse.ArgumentParser(
        description="Display the NexaTel SQLite schema and complete table contents."
    )
    parser.add_argument(
        "--table",
        action="append",
        dest="tables",
        help="Display only this table; repeat the option for multiple tables.",
    )
    options = parser.parse_args(arguments)

    connection = create_connection()
    try:
        available_tables = get_table_names(connection)
        selected_tables = options.tables or available_tables
        unknown_tables = sorted(set(selected_tables) - set(available_tables))

        if unknown_tables:
            parser.error(
                "Unknown table(s): " + ", ".join(unknown_tables)
            )

        print(f"DATABASE: {get_database_path()}")
        print(f"TABLES: {', '.join(selected_tables)}")

        for table_name in selected_tables:
            print_table(connection, table_name)
    finally:
        connection.close()


if __name__ == "__main__":
    main()