"""Customer-scoped full-record queries for the Customer 360 view."""

from __future__ import annotations

import sqlite3
from typing import Any


def get_customer_360_records(
    db: sqlite3.Connection,
    customer_id: str,
) -> dict[str, list[dict[str, Any]]]:
    """Return all rows associated with one trusted customer ID."""

    statements = {
        "customer": """
            SELECT customer_id, name, email, phone_number, city,
                   service_address_line, service_state,
                   service_postal_code,
                   account_status, registration_date
            FROM customers
            WHERE customer_id = ?
        """,
        "subscriptions": """
            SELECT subscription_id, customer_id, plan_id,
                   activation_date, status, renewal_date
            FROM subscriptions
            WHERE customer_id = ?
            ORDER BY activation_date DESC, subscription_id DESC
        """,
        "plans": """
            SELECT DISTINCT p.plan_id, p.plan_name, p.monthly_price,
                   p.data_limit_gb, p.is_data_unlimited,
                   p.voice_limit_minutes, p.sms_limit, p.plan_type
            FROM plans p
            JOIN subscriptions s ON s.plan_id = p.plan_id
            WHERE s.customer_id = ?
            ORDER BY p.plan_name, p.plan_id
        """,
        "usage": """
            SELECT usage_id, customer_id, subscription_id, usage_date,
                   data_used_gb, voice_minutes, sms_count
            FROM usage
            WHERE customer_id = ?
            ORDER BY usage_date DESC, usage_id DESC
        """,
        "bills": """
            SELECT bill_id, customer_id, subscription_id,
                   billing_period_start, billing_period_end,
                   amount, due_date, status
            FROM bills
            WHERE customer_id = ?
            ORDER BY billing_period_end DESC, bill_id DESC
        """,
        "bill_items": """
            SELECT i.bill_item_id, i.bill_id, i.description,
                   i.amount, i.item_type
            FROM bill_items i
            JOIN bills b ON b.bill_id = i.bill_id
            WHERE b.customer_id = ?
            ORDER BY b.billing_period_end DESC, i.bill_item_id
        """,
        "payments": """
            SELECT payment_id, bill_id, customer_id, amount,
                   payment_date, payment_method, status,
                   transaction_reference, failure_reason
            FROM payments
            WHERE customer_id = ?
            ORDER BY payment_date DESC, payment_id DESC
        """,
        "support_tickets": """
            SELECT ticket_id, customer_id, category, description,
                   status, priority, created_at, updated_at,
                   related_bill_id, related_payment_id
            FROM support_tickets
            WHERE customer_id = ?
            ORDER BY created_at DESC, ticket_id DESC
        """,
        "devices": """
            SELECT device_id, customer_id, device_name, device_type,
                   purchase_date, status
            FROM devices
            WHERE customer_id = ?
            ORDER BY purchase_date DESC, device_id DESC
        """,
    }

    return {
        name: [
            dict(row)
            for row in db.execute(
                sql,
                (customer_id,),
            ).fetchall()
        ]
        for name, sql in statements.items()
    }