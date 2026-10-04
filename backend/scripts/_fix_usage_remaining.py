from pathlib import Path

path = Path(__file__).resolve().parents[1] / "app/handlers/usage.py"
text = path.read_text(encoding="utf-8")

if "def _get_plan(" in text:
    raise SystemExit(0)

insert = '''

def _get_plan(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    plan_type: str | None = None,
):
    plan, error = resolve_usage_plan_row(
        db,
        customer.customer_id,
        plan_type=plan_type,
    )
    if error is not None:
        return None, error
    return plan, None


'''

text = text.replace(
    "def _get_period_totals(",
    insert + "def _get_period_totals(",
    1,
)

replacements = [
    (
        "        totals = _get_period_totals(\n"
        "            db,\n"
        "            customer,\n"
        "            period,\n"
        "        )",
        "        totals = _get_period_totals(\n"
        "            db,\n"
        "            customer,\n"
        "            period,\n"
        "            subscription_id=plan[\"subscription_id\"],\n"
        "        )",
    ),
    (
        "        primary = _get_period_totals(\n"
        "            db,\n"
        "            customer,\n"
        "            primary_period,\n"
        "        )\n\n"
        "        comparison = _get_period_totals(\n"
        "            db,\n"
        "            customer,\n"
        "            comparison_period,\n"
        "        )",
        "        plan, plan_error = _get_plan(\n"
        "            db,\n"
        "            customer,\n"
        "        )\n"
        "        if plan_error is not None:\n"
        "            return plan_error\n"
        "        assert plan is not None\n\n"
        "        primary = _get_period_totals(\n"
        "            db,\n"
        "            customer,\n"
        "            primary_period,\n"
        "            subscription_id=plan[\"subscription_id\"],\n"
        "        )\n\n"
        "        comparison = _get_period_totals(\n"
        "            db,\n"
        "            customer,\n"
        "            comparison_period,\n"
        "            subscription_id=plan[\"subscription_id\"],\n"
        "        )",
    ),
]

for old, new in replacements:
    if old in text:
        text = text.replace(old, new, 1)

text = text.replace(
    "        plan = _get_plan(\n"
    "            db,\n"
    "            customer,\n"
    "        )\n\n"
    "        totals = _get_period_totals(\n"
    "            db,\n"
    "            customer,\n"
    "            period,\n"
    "            subscription_id=plan[\"subscription_id\"],\n"
    "        )",
    "        plan, plan_error = _get_plan(\n"
    "            db,\n"
    "            customer,\n"
    "        )\n"
    "        if plan_error is not None:\n"
    "            return plan_error\n"
    "        assert plan is not None\n\n"
    "        totals = _get_period_totals(\n"
    "            db,\n"
    "            customer,\n"
    "            period,\n"
    "            subscription_id=plan[\"subscription_id\"],\n"
    "        )",
    1,
)

text = text.replace(
    "    if plan is None:\n"
    "        return not_found_result(\n"
    "            source=source_for_table(\n"
    "                \"subscriptions\"\n"
    "            ),\n"
    "            message=(\n"
    "                \"No subscription information \"\n"
    "                \"was found for your account.\"\n"
    "            ),\n"
    "        )\n\n"
    "    if totals[\"record_count\"] == 0:\n"
    "        return not_found_result(\n"
    "            source=source_for_table(\n"
    "                \"usage\"\n"
    "            ),\n"
    "            message=(\n"
    "                \"I don't have usage records for \"\n"
    "                f\"{_period_label(period)}.\"\n"
    "            ),\n"
    "        )\n\n"
    "    metrics = [",
    "    if totals[\"record_count\"] == 0:\n"
    "        return not_found_result(\n"
    "            source=source_for_table(\n"
    "                \"usage\"\n"
    "            ),\n"
    "            message=(\n"
    "                \"I don't have usage records for \"\n"
    "                f\"{_period_label(period)}.\"\n"
    "            ),\n"
    "        )\n\n"
    "    metrics = [",
    1,
)

path.write_text(text, encoding="utf-8")
