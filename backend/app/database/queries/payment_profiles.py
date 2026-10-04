"""Customer payment profile queries."""

from __future__ import annotations

import sqlite3


def get_payment_profile(
    db: sqlite3.Connection,
    customer_id: str,
) -> sqlite3.Row | None:
    """Return autopay and payment-on-file details for one customer."""

    return db.execute(
        """
        SELECT
            customer_id,
            autopay_enabled,
            default_payment_method,
            payment_method_label
        FROM customer_payment_profiles
        WHERE customer_id = ?
        """,
        (customer_id,),
    ).fetchone()
