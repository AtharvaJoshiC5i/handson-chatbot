from pathlib import Path

path = Path(__file__).resolve().parents[1] / "app/handlers/usage.py"
text = path.read_text(encoding="utf-8")

if "resolve_usage_plan_row" in text:
    raise SystemExit(0)

text = text.replace(
    "from app.database.queries.usage import (\n"
    "    get_customer_usage_plan,\n"
    "    get_monthly_usage_totals,\n"
    "    get_usage_totals_by_date_range,\n"
    ")\n",
    "from app.business.subscription_scope import (\n"
    "    resolve_usage_plan_row,\n"
    ")\n"
    "from app.database.queries.usage import (\n"
    "    get_monthly_usage_totals,\n"
    "    get_usage_totals_by_date_range,\n"
    ")\n",
)

text = text.replace(
    "def _get_plan(\n"
    "    db: sqlite3.Connection,\n"
    "    customer: CustomerContext,\n"
    "):\n"
    "    return get_customer_usage_plan(\n"
    "        db,\n"
    "        customer.customer_id,\n"
    "    )\n\n\n"
    "def _get_period_totals(\n"
    "    db: sqlite3.Connection,\n"
    "    customer: CustomerContext,\n"
    "    period: DateRange,\n"
    "):\n"
    "    return get_usage_totals_by_date_range(\n"
    "        db,\n"
    "        customer.customer_id,\n"
    "        period.start_date.isoformat(),\n"
    "        period.end_date.isoformat(),\n"
    "    )\n",
    "def _get_period_totals(\n"
    "    db: sqlite3.Connection,\n"
    "    customer: CustomerContext,\n"
    "    period: DateRange,\n"
    "    *,\n"
    "    subscription_id: str | None,\n"
    "):\n"
    "    return get_usage_totals_by_date_range(\n"
    "        db,\n"
    "        customer.customer_id,\n"
    "        period.start_date.isoformat(),\n"
    "        period.end_date.isoformat(),\n"
    "        subscription_id=subscription_id,\n"
    "    )\n",
)

old_single = """def _single_usage(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    usage_type: UsageType,
    time_range: TimeRange | None = None,
    month: int | None = None,
    year: int | None = None,
) -> TruthResult[dict]:
    period, error = _resolve_period(
        time_range=time_range,
        month=month,
        year=year,
    )

    if error is not None:
        return error

    try:
        plan = _get_plan(
            db,
            customer,
        )

        totals = _get_period_totals(
            db,
            customer,
            period,
        )
"""

new_single = """def _single_usage(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    usage_type: UsageType,
    time_range: TimeRange | None = None,
    month: int | None = None,
    year: int | None = None,
    plan_type: str | None = None,
) -> TruthResult[dict]:
    period, error = _resolve_period(
        time_range=time_range,
        month=month,
        year=year,
    )

    if error is not None:
        return error

    plan, plan_error = resolve_usage_plan_row(
        db,
        customer.customer_id,
        plan_type=plan_type,
    )

    if plan_error is not None:
        return plan_error

    assert plan is not None

    try:
        totals = _get_period_totals(
            db,
            customer,
            period,
            subscription_id=plan["subscription_id"],
        )
"""

if old_single not in text:
    raise RuntimeError("_single_usage block not found")

text = text.replace(old_single, new_single)

for fn in (
    "get_data_usage",
    "get_voice_usage",
    "get_sms_usage",
):
    text = text.replace(
        f"def {fn}(\n"
        "    db: sqlite3.Connection,\n"
        "    customer: CustomerContext,\n"
        "    *,\n"
        "    time_range: TimeRange | None = None,\n"
        "    month: int | None = None,\n"
        "    year: int | None = None,\n"
        ") -> TruthResult[dict]:\n"
        "    return _single_usage(\n"
        "        db,\n"
        "        customer,\n"
        "        usage_type=UsageType.",
        f"def {fn}(\n"
        "    db: sqlite3.Connection,\n"
        "    customer: CustomerContext,\n"
        "    *,\n"
        "    time_range: TimeRange | None = None,\n"
        "    month: int | None = None,\n"
        "    year: int | None = None,\n"
        "    plan_type: str | None = None,\n"
        ") -> TruthResult[dict]:\n"
        "    return _single_usage(\n"
        "        db,\n"
        "        customer,\n"
        "        usage_type=UsageType.",
    )

# pass plan_type into _single_usage calls for data/voice/sms
for usage in ("DATA", "VOICE", "SMS"):
    text = text.replace(
        f"usage_type=UsageType.{usage},\n"
        "        time_range=time_range,\n"
        "        month=month,\n"
        "        year=year,\n"
        "    )",
        f"usage_type=UsageType.{usage},\n"
        "        time_range=time_range,\n"
        "        month=month,\n"
        "        year=year,\n"
        "        plan_type=plan_type,\n"
        "    )",
        1,
    )

path.write_text(text, encoding="utf-8")
print("patched usage handlers")
