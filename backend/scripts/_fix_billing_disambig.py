from pathlib import Path

path = Path(__file__).resolve().parents[1] / "app/handlers/billing.py"
text = path.read_text(encoding="utf-8")
if "resolve_billing_plan_type" in text:
    raise SystemExit(0)
text = text.replace(
    "from app.database.queries.bills import (",
    "from app.business.subscription_scope import (\n"
    "    resolve_billing_plan_type,\n"
    ")\n"
    "from app.database.queries.bills import (",
)
text = text.replace(
    "def get_current_bill(\n"
    "    db: sqlite3.Connection,\n"
    "    customer: CustomerContext,\n"
    "    *,\n"
    "    plan_type: str | None = None,\n"
    ") -> TruthResult[dict]:\n"
    "    try:\n"
    "        bill = get_latest_bill(",
    "def get_current_bill(\n"
    "    db: sqlite3.Connection,\n"
    "    customer: CustomerContext,\n"
    "    *,\n"
    "    plan_type: str | None = None,\n"
    ") -> TruthResult[dict]:\n"
    "    ambiguity = resolve_billing_plan_type(\n"
    "        db,\n"
    "        customer.customer_id,\n"
    "        plan_type=plan_type,\n"
    "    )\n"
    "    if ambiguity is not None:\n"
    "        return ambiguity\n\n"
    "    try:\n"
    "        bill = get_latest_bill(",
)
path.write_text(text, encoding="utf-8")

client = Path(__file__).resolve().parents[1] / "app/llm/client.py"
ct = client.read_text(encoding="utf-8")
if "PlanType," not in ct.split("from app.models.domain import")[1][:200]:
    ct = ct.replace(
        "    Intent,\n",
        "    Intent,\n    PlanType,\n",
        1,
    )
    client.write_text(ct, encoding="utf-8")

phase0 = Path(__file__).resolve().parents[1] / "tests/integration/test_phase0_dataset.py"
pt = phase0.read_text(encoding="utf-8")
pt = pt.replace(
    '    "devices",\n}',
    '    "devices",\n    "customer_payment_profiles",\n    "account_credits",\n}',
)
phase0.write_text(pt, encoding="utf-8")

guard = Path(__file__).resolve().parents[1] / "tests/unit/test_prompt_guard_classifier.py"
gt = guard.read_text(encoding="utf-8")
gt = gt.replace(
    "def test_classifier_routes_phone_bill_to_device_filter_not_unsupported() -> None:\n"
    "    phone_bill = classify_prompt_guard_request(\"Show me my phone bill\")\n\n"
    "    assert phone_bill.intent == Intent.FILTER_DEVICES\n",
    "def test_classifier_routes_phone_bill_to_current_mobile_bill() -> None:\n"
    "    phone_bill = classify_prompt_guard_request(\"Show me my phone bill\")\n\n"
    "    assert phone_bill.intent == Intent.GET_CURRENT_BILL\n"
    "    assert phone_bill.parameters.plan_type is not None\n",
)
guard.write_text(gt, encoding="utf-8")
