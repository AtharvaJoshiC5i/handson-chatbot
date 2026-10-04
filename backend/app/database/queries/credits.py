"""Account credit queries."""

from __future__ import annotations

import sqlite3


def list_account_credits(
    db: sqlite3.Connection,
    customer_id: str,
) -> list[sqlite3.Row]:
    """Return credits for one customer, newest first."""

    return db.execute(
        """
        SELECT
            credit_id,
            customer_id,
            amount,
            reason,
            credit_date,
            status
        FROM account_credits
        WHERE customer_id = ?
        ORDER BY credit_date DESC, credit_id DESC
        """,
        (customer_id,),
    ).fetchall()


def get_available_credit_total(
    db: sqlite3.Connection,
    customer_id: str,
) -> float:
    """Sum AVAILABLE credits for one customer."""

    row = db.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM account_credits
        WHERE customer_id = ?
          AND status = 'AVAILABLE'
        """,
        (customer_id,),
    ).fetchone()

    return float(row["total"] if row else 0)
