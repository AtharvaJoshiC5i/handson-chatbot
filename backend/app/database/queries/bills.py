"""Deterministic billing queries for NexaTel."""

from __future__ import annotations

from datetime import date
import sqlite3

_BILL_SELECT = """
    b.bill_id,
    b.customer_id,
    b.subscription_id,
    b.billing_period_start,
    b.billing_period_end,
    b.amount,
    b.due_date,
    b.status,
    p.plan_type
"""

_BILL_FROM = """
    FROM bills b
    JOIN subscriptions s
      ON b.subscription_id = s.subscription_id
    JOIN plans p
      ON s.plan_id = p.plan_id
"""


def _plan_type_clause(
    plan_type: str | None,
) -> tuple[str, list[object]]:
    if plan_type is None:
        return "", []

    return (
        " AND p.plan_type = ?",
        [plan_type],
    )


def get_latest_bill(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    plan_type: str | None = None,
) -> sqlite3.Row | None:
    """Return the customer's latest available bill."""

    plan_clause, plan_params = _plan_type_clause(
        plan_type,
    )

    return db.execute(
        f"""
        SELECT
            {_BILL_SELECT}
        {_BILL_FROM}
        WHERE b.customer_id = ?
        {plan_clause}
        ORDER BY
            b.billing_period_end DESC,
            b.bill_id DESC
        LIMIT 1
        """,
        (customer_id, *plan_params),
    ).fetchone()


def get_current_statement_bill(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    plan_type: str | None = None,
    as_of: date | None = None,
) -> sqlite3.Row | None:
    """
    Latest bill whose billing period has ended (statement bill).

    In-progress cycle bills (period end after today) are excluded so
    "current bill" aligns with the latest closed statement month.
    """

    reference_date = (
        as_of or date.today()
    ).isoformat()

    plan_clause, plan_params = _plan_type_clause(
        plan_type,
    )

    return db.execute(
        f"""
        SELECT
            {_BILL_SELECT}
        {_BILL_FROM}
        WHERE b.customer_id = ?
          AND b.billing_period_end <= ?
        {plan_clause}
        ORDER BY
            b.billing_period_end DESC,
            b.bill_id DESC
        LIMIT 1
        """,
        (
            customer_id,
            reference_date,
            *plan_params,
        ),
    ).fetchone()


def get_bill_by_id_for_customer(
    db: sqlite3.Connection,
    customer_id: str,
    bill_id: str,
) -> sqlite3.Row | None:
    """Return a bill only if it belongs to the customer."""

    return db.execute(
        f"""
        SELECT
            {_BILL_SELECT}
        {_BILL_FROM}
        WHERE b.customer_id = ?
          AND b.bill_id = ?
        LIMIT 1
        """,
        (
            customer_id,
            bill_id,
        ),
    ).fetchone()


def get_bill_for_month(
    db: sqlite3.Connection,
    customer_id: str,
    year: int,
    month: int,
    *,
    plan_type: str | None = None,
) -> sqlite3.Row | None:
    """Return the customer's bill covering the requested month."""

    period = (
        f"{year}-{month:02d}"
    )

    plan_clause, plan_params = _plan_type_clause(
        plan_type,
    )

    return db.execute(
        f"""
        SELECT
            {_BILL_SELECT}
        {_BILL_FROM}
        WHERE b.customer_id = ?
          AND substr(
                b.billing_period_start,
                1,
                7
              ) = ?
        {plan_clause}
        ORDER BY b.billing_period_end DESC
        LIMIT 1
        """,
        (
            customer_id,
            period,
            *plan_params,
        ),
    ).fetchone()


def get_previous_bill(
    db: sqlite3.Connection,
    customer_id: str,
    before_period_start: str,
    *,
    plan_type: str | None = None,
) -> sqlite3.Row | None:
    """Return the bill immediately before a supplied bill period."""

    plan_clause, plan_params = _plan_type_clause(
        plan_type,
    )

    return db.execute(
        f"""
        SELECT
            {_BILL_SELECT}
        {_BILL_FROM}
        WHERE b.customer_id = ?
          AND b.billing_period_start < ?
        {plan_clause}
        ORDER BY
            b.billing_period_start DESC,
            b.bill_id DESC
        LIMIT 1
        """,
        (
            customer_id,
            before_period_start,
            *plan_params,
        ),
    ).fetchone()


def get_bill_history(
    db: sqlite3.Connection,
    customer_id: str,
    limit: int | None = None,
    *,
    plan_type: str | None = None,
) -> list[sqlite3.Row]:
    """Return bill history newest first."""

    plan_clause, plan_params = _plan_type_clause(
        plan_type,
    )

    sql = f"""
        SELECT
            {_BILL_SELECT}
        {_BILL_FROM}
        WHERE b.customer_id = ?
        {plan_clause}
        ORDER BY
            b.billing_period_start DESC,
            b.bill_id DESC
    """

    parameters: list[object] = [
        customer_id,
        *plan_params,
    ]

    if limit is not None:
        sql += "\nLIMIT ?"
        parameters.append(limit)

    return db.execute(
        sql,
        tuple(parameters),
    ).fetchall()


def get_bills_for_date_range(
    db: sqlite3.Connection,
    customer_id: str,
    start_date: str,
    end_date: str,
    *,
    plan_type: str | None = None,
) -> list[sqlite3.Row]:
    """Return bills whose period starts within a date range."""

    plan_clause, plan_params = _plan_type_clause(
        plan_type,
    )

    return db.execute(
        f"""
        SELECT
            {_BILL_SELECT}
        {_BILL_FROM}
        WHERE b.customer_id = ?
          AND b.billing_period_start >= ?
          AND b.billing_period_start <= ?
        {plan_clause}
        ORDER BY b.billing_period_start ASC
        """,
        (
            customer_id,
            start_date,
            end_date,
            *plan_params,
        ),
    ).fetchall()


def get_bill_items(
    db: sqlite3.Connection,
    bill_id: str,
) -> list[sqlite3.Row]:
    """Return all itemized charges belonging to a bill."""

    return db.execute(
        """
        SELECT
            bill_item_id,
            bill_id,
            description,
            amount,
            item_type
        FROM bill_items
        WHERE bill_id = ?
        ORDER BY bill_item_id ASC
        """,
        (bill_id,),
    ).fetchall()


def get_filtered_bills(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    status: str | None = None,
    minimum_amount: float | None = None,
    limit: int | None = None,
    sort_order: str = "NEWEST",
    plan_type: str | None = None,
) -> list[sqlite3.Row]:
    """Return customer-owned bills using controlled billing filters."""

    conditions = [
        "b.customer_id = ?"
    ]

    parameters: list[object] = [
        customer_id,
    ]

    plan_clause, plan_params = _plan_type_clause(
        plan_type,
    )

    parameters.extend(plan_params)

    if status is not None:
        conditions.append(
            "b.status = ?"
        )

        parameters.append(
            status
        )

    if minimum_amount is not None:
        conditions.append(
            "b.amount >= ?"
        )

        parameters.append(
            minimum_amount
        )

    order_by = {
        "NEWEST": (
            "b.billing_period_start DESC, "
            "b.bill_id DESC"
        ),
        "OLDEST": (
            "b.billing_period_start ASC, "
            "b.bill_id ASC"
        ),
        "AMOUNT_HIGH_TO_LOW": (
            "b.amount DESC, "
            "b.billing_period_start DESC"
        ),
        "AMOUNT_LOW_TO_HIGH": (
            "b.amount ASC, "
            "b.billing_period_start DESC"
        ),
    }.get(
        sort_order,
        "b.billing_period_start DESC, b.bill_id DESC",
    )

    sql = f"""
        SELECT
            {_BILL_SELECT}
        {_BILL_FROM}
        WHERE {" AND ".join(conditions)}
        {plan_clause}
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


def get_non_paid_bills(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    limit: int | None = None,
    plan_type: str | None = None,
    sort_order: str = "NEWEST",
) -> list[sqlite3.Row]:
    """Bills that are unpaid, overdue, or partially paid."""

    conditions = [
        "b.customer_id = ?",
        "b.status IN ('UNPAID', 'OVERDUE', 'PARTIALLY_PAID')",
    ]
    parameters: list[object] = [customer_id]
    plan_clause, plan_params = _plan_type_clause(plan_type)
    parameters.extend(plan_params)

    order_by = {
        "NEWEST": (
            "b.billing_period_start DESC, "
            "b.bill_id DESC"
        ),
        "OLDEST": (
            "b.billing_period_start ASC, "
            "b.bill_id ASC"
        ),
    }.get(
        sort_order,
        "b.billing_period_start DESC, b.bill_id DESC",
    )

    sql = f"""
        SELECT
            {_BILL_SELECT}
        {_BILL_FROM}
        WHERE {" AND ".join(conditions)}
        {plan_clause}
        ORDER BY {order_by}
    """

    if limit is not None:
        sql += "\nLIMIT ?"
        parameters.append(limit)

    return db.execute(
        sql,
        tuple(parameters),
    ).fetchall()


def get_bill_item_total(
    db: sqlite3.Connection,
    bill_id: str,
) -> sqlite3.Row:
    """Return bill-item count and deterministic item total."""

    return db.execute(
        """
        SELECT
            COUNT(*) AS item_count,
            COALESCE(SUM(amount), 0) AS item_total
        FROM bill_items
        WHERE bill_id = ?
        """,
        (bill_id,),
    ).fetchone()


def sum_bill_items_by_type(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    item_type: str,
    month_count: int | None = None,
    plan_type: str | None = None,
) -> sqlite3.Row:
    """
    Sum bill line items of one type across recent bills.
    """

    plan_clause, plan_params = _plan_type_clause(
        plan_type,
    )

    sql = f"""
        SELECT
            COUNT(DISTINCT b.bill_id) AS bill_count,
            COALESCE(SUM(i.amount), 0) AS total_amount
        FROM bill_items i
        JOIN bills b
          ON b.bill_id = i.bill_id
        JOIN subscriptions s
          ON s.subscription_id = b.subscription_id
        JOIN plans p
          ON p.plan_id = s.plan_id
        WHERE b.customer_id = ?
          AND i.item_type = ?
        {plan_clause}
    """

    params: list[object] = [
        customer_id,
        item_type,
        *plan_params,
    ]

    if month_count is not None:
        sql += """
          AND b.billing_period_start >= (
              SELECT MIN(recent.billing_period_start)
              FROM (
                  SELECT billing_period_start
                  FROM bills
                  WHERE customer_id = ?
                  ORDER BY billing_period_start DESC
                  LIMIT ?
              ) recent
          )
        """
        params.extend(
            [
                customer_id,
                month_count,
            ]
        )

    return db.execute(
        sql,
        tuple(params),
    ).fetchone()


def list_bill_items_for_customer(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    bill_id: str | None = None,
    item_type: str | None = None,
    limit: int = 25,
) -> list[sqlite3.Row]:
    """Return bill line items scoped to one customer."""

    clauses = ["b.customer_id = ?"]
    params: list[object] = [customer_id]

    if bill_id is not None:
        clauses.append("i.bill_id = ?")
        params.append(bill_id)

    if item_type is not None:
        clauses.append("i.item_type = ?")
        params.append(item_type)

    params.append(limit)

    return db.execute(
        f"""
        SELECT
            i.bill_item_id,
            i.bill_id,
            i.description,
            i.amount,
            i.item_type
        FROM bill_items i
        JOIN bills b
          ON b.bill_id = i.bill_id
        WHERE {" AND ".join(clauses)}
        ORDER BY b.billing_period_end DESC, i.bill_item_id ASC
        LIMIT ?
        """,
        params,
    ).fetchall()
