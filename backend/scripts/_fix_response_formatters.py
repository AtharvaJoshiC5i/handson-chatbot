from pathlib import Path

path = Path(__file__).resolve().parents[1] / "app/services/response_service.py"
text = path.read_text(encoding="utf-8")
if "def _format_subscription_list" in text:
    raise SystemExit(0)

block = '''

def _format_subscription_list(data: dict) -> str:
    lines = [
        f"You have {data['count']} subscription(s) on your account:",
    ]
    for sub in data["subscriptions"]:
        lines.append(
            f"- {sub['plan_name']} ({sub['plan_type']}): "
            f"{sub['status']}, renews {sub['renewal_date']}"
        )
    return " ".join(lines)


def _format_plan_catalog(data: dict) -> str:
    lines = [f"{data['count']} NexaTel plan(s) available:"]
    for plan in data["plans"]:
        data_label = (
            "unlimited data"
            if plan["is_data_unlimited"]
            else f"{plan['data_limit_gb']} GB data"
        )
        lines.append(
            f"- {plan['plan_name']} ({plan['plan_type']}): "
            f"₹{plan['monthly_price']}/month, {data_label}"
        )
    return " ".join(lines)


def _format_plan_comparison(data: dict) -> str:
    left = data["current"]
    right = data["previous"]
    return (
        f"{left['plan_name']} (₹{left['monthly_price']}) vs "
        f"{right['plan_name']} (₹{right['monthly_price']}). "
        f"Data limits: {left['data_limit_gb']} GB vs "
        f"{right['data_limit_gb']} GB."
    )


def _format_bill_charge_summary(data: dict) -> str:
    scope = (
        f" across your last {data['month_count']} bills"
        if data.get("month_count")
        else ""
    )
    return (
        f"Total {data['item_type'].replace('_', ' ').lower()} "
        f"charges{scope}: ₹{data['total_amount']} "
        f"from {data['bill_count']} bill(s)."
    )


def _format_projected_bill(data: dict) -> str:
    return (
        f"Estimated {data['plan_name']} bill as of "
        f"{data['as_of_date']}: ₹{data['estimated_amount']} "
        f"(plan price ₹{data['base_plan_amount']}). "
        f"{data['note']}"
    )


def _format_payment_profile(data: dict) -> str:
    autopay = (
        "enabled" if data["autopay_enabled"] else "disabled"
    )
    label = data.get("payment_method_label") or "not on file"
    method = data.get("default_payment_method") or "none"
    return (
        f"Autopay is {autopay}. Default payment method: "
        f"{method} ({label})."
    )


def _format_account_credits(data: dict) -> str:
    if data["available_total"] <= 0:
        return "You have no available account credits."
    return (
        f"Available credit balance: ₹{data['available_total']}. "
        f"{len(data['credits'])} credit record(s) on file."
    )

'''

text = text.replace(
    "# ============================================================\n"
    "# RESULT TYPE DISPATCH\n"
    "# ============================================================\n\n\n"
    "FORMATTERS = {",
    block
    + "\n# ============================================================\n"
    "# RESULT TYPE DISPATCH\n"
    "# ============================================================\n\n\n"
    "FORMATTERS = {",
)
path.write_text(text, encoding="utf-8")
