from app.database.connection import create_connection


def main() -> None:
    connection = create_connection()

    try:
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        print("\nTables:")
        for row in tables:
            print(f"  - {row['name']}")

        print("\nRecord counts:")

        for table in [
            "customers",
            "plans",
            "subscriptions",
            "usage",
            "bills",
            "bill_items",
            "payments",
            "support_tickets",
            "devices",
        ]:
            row = connection.execute(
                f"SELECT COUNT(*) AS count FROM {table}"
            ).fetchone()

            print(f"  {table}: {row['count']}")

        print("\nForeign keys:")
        foreign_keys = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()

        print(f"  enabled = {foreign_keys[0] == 1}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()