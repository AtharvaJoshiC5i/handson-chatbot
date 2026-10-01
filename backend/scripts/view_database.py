"""Print the complete NexaTel SQLite database in a readable table format."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Any, Sequence

# Allow `python scripts/view_database.py` from the backend directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.connection import create_connection, get_database_path


def get_table_names(connection: sqlite3.Connection) -> list[str]:
    """Return all application tables."""

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
    """Safely quote a SQLite identifier."""

    return '"' + identifier.replace('"', '""') + '"'


def format_value(value: Any) -> str:
    """Convert a database value into a printable string."""

    if value is None:
        return "NULL"

    if isinstance(value, bytes):
        return value.hex()

    # Keep each database row on a single terminal line.
    return str(value).replace("\n", "\\n").replace("\r", "\\r")


def build_separator(
    widths: list[int],
    left: str = "+",
    middle: str = "+",
    right: str = "+",
    fill: str = "-",
) -> str:
    """Build a horizontal table separator."""

    return (
        left
        + middle.join(fill * (width + 2) for width in widths)
        + right
    )


def build_row(values: list[str], widths: list[int]) -> str:
    """Build one formatted table row."""

    cells = [
        f" {value:<{width}} "
        for value, width in zip(values, widths)
    ]

    return "|" + "|".join(cells) + "|"


def print_rows_as_table(
    column_names: list[str],
    rows: list[sqlite3.Row],
) -> None:
    """Print SQLite rows as an aligned terminal table."""

    formatted_rows = [
        [format_value(row[column]) for column in column_names]
        for row in rows
    ]

    widths = []

    for index, column_name in enumerate(column_names):
        width = len(column_name)

        for row in formatted_rows:
            width = max(width, len(row[index]))

        widths.append(width)

    separator = build_separator(widths)

    print(separator)
    print(build_row(column_names, widths))
    print(separator)

    for row in formatted_rows:
        print(build_row(row, widths))

    print(separator)


def print_schema(columns: list[sqlite3.Row]) -> None:
    """Print table schema information in table format."""

    headers = [
        "Column",
        "Type",
        "Nullable",
        "Primary Key",
        "Default",
    ]

    schema_rows = []

    for column in columns:
        schema_rows.append(
            {
                "Column": column["name"],
                "Type": column["type"] or "ANY",
                "Nullable": "NO" if column["notnull"] else "YES",
                "Primary Key": "YES" if column["pk"] else "NO",
                "Default": (
                    str(column["dflt_value"])
                    if column["dflt_value"] is not None
                    else "NULL"
                ),
            }
        )

    widths = []

    for header in headers:
        widths.append(
            max(
                len(header),
                max(
                    (len(row[header]) for row in schema_rows),
                    default=0,
                ),
            )
        )

    separator = build_separator(widths)

    print(separator)
    print(build_row(headers, widths))
    print(separator)

    for row in schema_rows:
        print(
            build_row(
                [row[header] for header in headers],
                widths,
            )
        )

    print(separator)


def print_table(
    connection: sqlite3.Connection,
    table_name: str,
) -> None:
    """Print schema details and all rows for one database table."""

    columns = connection.execute(
        f"PRAGMA table_info({quote_identifier(table_name)})"
    ).fetchall()

    rows = connection.execute(
        f"SELECT * FROM {quote_identifier(table_name)}"
    ).fetchall()

    print()
    print("=" * 100)
    print(f"TABLE: {table_name}")
    print(f"ROWS : {len(rows)}")
    print("=" * 100)

    print("\nSCHEMA")
    print_schema(columns)

    print("\nDATA")

    if not rows:
        print("<empty>")
        return

    column_names = [column["name"] for column in columns]

    print_rows_as_table(
        column_names=column_names,
        rows=rows,
    )


def main(arguments: Sequence[str] | None = None) -> None:
    """Display all database tables or selected tables."""

    parser = argparse.ArgumentParser(
        description=(
            "Display the NexaTel SQLite database "
            "schema and table contents."
        )
    )

    parser.add_argument(
        "--table",
        action="append",
        dest="tables",
        help=(
            "Display only this table. "
            "Repeat --table to display multiple tables."
        ),
    )

    options = parser.parse_args(arguments)

    connection = create_connection()

    # Required so rows can be accessed using column names.
    connection.row_factory = sqlite3.Row

    try:
        available_tables = get_table_names(connection)

        selected_tables = (
            options.tables
            if options.tables
            else available_tables
        )

        unknown_tables = sorted(
            set(selected_tables) - set(available_tables)
        )

        if unknown_tables:
            parser.error(
                "Unknown table(s): "
                + ", ".join(unknown_tables)
            )

        print()
        print("=" * 100)
        print("NEXATEL DATABASE VIEWER")
        print("=" * 100)
        print(f"Database : {get_database_path()}")
        print(f"Tables   : {', '.join(selected_tables)}")
        print(f"Count    : {len(selected_tables)}")

        for table_name in selected_tables:
            print_table(
                connection=connection,
                table_name=table_name,
            )

        print()
        print("=" * 100)
        print("END OF DATABASE")
        print("=" * 100)

    finally:
        connection.close()


if __name__ == "__main__":
    main()