from __future__ import annotations

import sqlite3

from app.database.seed import seed_database


TABLES = {
    "customers",
    "plans",
    "subscriptions",
    "usage",
    "bills",
    "bill_items",
    "payments",
    "support_tickets",
    "devices",
}


def _db() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row

    db.execute(
        "PRAGMA foreign_keys = ON"
    )

    seed_database(
        db,
        reset=True,
    )

    return db


def test_phase0_tables_and_counts():
    db = _db()

    names = {
        row[0]
        for row in db.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            """
        )
    }

    assert names == TABLES

    assert (
        db.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]
        == 20
    )

    assert (
        db.execute(
            "SELECT COUNT(*) FROM usage"
        ).fetchone()[0]
        >= 300
    )

    assert (
        db.execute(
            "SELECT COUNT(*) FROM bills"
        ).fetchone()[0]
        >= 100
    )

    assert (
        db.execute(
            "SELECT COUNT(*) FROM support_tickets"
        ).fetchone()[0]
        >= 30
    )


def test_foreign_keys_and_cross_table_ownership():
    db = _db()

    assert (
        db.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()
        == []
    )

    usage_mismatch = db.execute(
        """
        SELECT COUNT(*)
        FROM usage u
        JOIN subscriptions s
          ON s.subscription_id = u.subscription_id
        WHERE u.customer_id <> s.customer_id
        """
    ).fetchone()[0]

    assert usage_mismatch == 0

    payment_mismatch = db.execute(
        """
        SELECT COUNT(*)
        FROM payments p
        JOIN bills b
          ON b.bill_id = p.bill_id
        WHERE p.customer_id <> b.customer_id
        """
    ).fetchone()[0]

    assert payment_mismatch == 0


def test_bill_totals_and_paid_statuses_are_consistent():
    db = _db()

    mismatches = db.execute(
        """
        SELECT b.bill_id
        FROM bills b
        JOIN bill_items i
          ON i.bill_id = b.bill_id
        GROUP BY b.bill_id
        HAVING ABS(
            b.amount - SUM(i.amount)
        ) > 0.001
        """
    ).fetchall()

    assert mismatches == []

    unsupported_paid_bills = db.execute(
        """
        SELECT b.bill_id
        FROM bills b
        LEFT JOIN payments p
          ON p.bill_id = b.bill_id
         AND p.status = 'SUCCESS'
        WHERE b.status = 'PAID'
        GROUP BY b.bill_id
        HAVING
            COALESCE(SUM(p.amount), 0) + 0.001
            < b.amount
        """
    ).fetchall()

    assert unsupported_paid_bills == []


def test_temporal_consistency_and_unlimited_fiber():
    db = _db()

    usage_before_activation = db.execute(
        """
        SELECT COUNT(*)
        FROM usage u
        JOIN subscriptions s
          ON s.subscription_id = u.subscription_id
        WHERE u.usage_date < s.activation_date
        """
    ).fetchone()[0]

    assert usage_before_activation == 0

    invalid_ticket_dates = db.execute(
        """
        SELECT COUNT(*)
        FROM support_tickets
        WHERE updated_at < created_at
        """
    ).fetchone()[0]

    assert invalid_ticket_dates == 0

    post_cancellation_usage = db.execute(
        """
        SELECT COUNT(*)
        FROM usage u
        JOIN subscriptions s
          ON s.subscription_id = u.subscription_id
        WHERE s.status = 'CANCELLED'
          AND u.usage_date > s.renewal_date
        """
    ).fetchone()[0]

    assert post_cancellation_usage == 0

    unlimited_fiber = db.execute(
        """
        SELECT COUNT(*)
        FROM plans
        WHERE plan_type = 'FIBER'
          AND is_data_unlimited = 1
          AND data_limit_gb = 0
        """
    ).fetchone()[0]

    assert unlimited_fiber >= 1

    ambiguous_fiber = db.execute(
        """
        SELECT COUNT(*)
        FROM plans
        WHERE plan_type = 'FIBER'
          AND is_data_unlimited = 0
          AND data_limit_gb = 0
        """
    ).fetchone()[0]

    assert ambiguous_fiber == 0


def test_unique_ids_and_transaction_references():
    db = _db()

    keys = [
        ("customers", "customer_id"),
        ("plans", "plan_id"),
        ("subscriptions", "subscription_id"),
        ("usage", "usage_id"),
        ("bills", "bill_id"),
        ("bill_items", "bill_item_id"),
        ("payments", "payment_id"),
        ("support_tickets", "ticket_id"),
        ("devices", "device_id"),
    ]

    for table, key in keys:
        total, unique = db.execute(
            f"""
            SELECT
                COUNT(*),
                COUNT(DISTINCT {key})
            FROM {table}
            """
        ).fetchone()

        assert total == unique

    total, unique = db.execute(
        """
        SELECT
            COUNT(*),
            COUNT(DISTINCT transaction_reference)
        FROM payments
        """
    ).fetchone()

    assert total == unique


def test_primary_demo_customers_have_historical_coverage():
    db = _db()

    demo_customers = (
        "CUST002",
        "CUST003",
        "CUST004",
        "CUST005",
        "CUST006",
    )

    for customer_id in demo_customers:
        usage_months = db.execute(
            """
            SELECT COUNT(
                DISTINCT substr(usage_date, 1, 7)
            )
            FROM usage
            WHERE customer_id = ?
            """,
            (customer_id,),
        ).fetchone()[0]

        assert usage_months >= 6

        bill_count = db.execute(
            """
            SELECT COUNT(*)
            FROM bills
            WHERE customer_id = ?
            """,
            (customer_id,),
        ).fetchone()[0]

        assert bill_count >= 6