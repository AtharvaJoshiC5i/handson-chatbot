from pathlib import Path

path = Path(__file__).resolve().parents[1] / "app/database/queries/bills.py"
text = path.read_text(encoding="utf-8")
if "sum_bill_items_by_type" in text:
    raise SystemExit(0)

append = '''

def sum_bill_items_by_type(
    db: sqlite3.Connection,
    customer_id: str,
    *,
    item_type: str,
    month_count: int | None = None,
    plan_type: str | None = None,
) -> sqlite3.Row:
    """Sum bill line items of one type across recent bills."""

    plan_clause, plan_params = _plan_type_clause(plan_type)
    sql = f"""
        SELECT
            COUNT(DISTINCT b.bill_id) AS bill_count,
            COALESCE(SUM(i.amount), 0) AS total_amount
        FROM bill_items i
        JOIN bills b ON b.bill_id = i.bill_id
        JOIN subscriptions s ON s.subscription_id = b.subscription_id
        JOIN plans p ON p.plan_id = s.plan_id
        WHERE b.customer_id = ?
          AND i.item_type = ?
        {plan_clause}
    """
    params: list[object] = [customer_id, item_type, *plan_params]
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
        params.extend([customer_id, month_count])
    return db.execute(sql, tuple(params)).fetchone()
'''
path.write_text(text + append, encoding="utf-8")
