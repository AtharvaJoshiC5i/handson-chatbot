"""Wire new intents, parameters, router, seed, and formatters."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch_parameters() -> None:
    path = ROOT / "app/intent/parameters.py"
    text = path.read_text(encoding="utf-8")
    if "BillItemType" in text:
        return
    text = text.replace(
        "    BillExtremeType,\n"
        "    BillSortOrder,\n"
        "    BillStatus,\n",
        "    BillExtremeType,\n"
        "    BillItemType,\n"
        "    BillSortOrder,\n"
        "    BillStatus,\n",
    )
    text = text.replace(
        '        "plan_type": (\n            PlanType\n        ),\n',
        '        "plan_type": (\n            PlanType\n        ),\n'
        '        "bill_item_type": (\n            BillItemType\n        ),\n',
    )
    path.write_text(text, encoding="utf-8")


def patch_definitions() -> None:
    path = ROOT / "app/intent/definitions.py"
    text = path.read_text(encoding="utf-8")
    if "get_list_subscriptions" in text:
        return
    insert = """
    _definition(
        Intent.GET_LIST_SUBSCRIPTIONS,
        "get_list_subscriptions",
    ),
    _definition(
        Intent.GET_PLAN_CATALOG,
        "get_plan_catalog",
        optional=PLAN_TYPE,
    ),
    _definition(
        Intent.GET_PLAN_COMPARISON,
        "get_plan_comparison",
        required=(
            "plan_id",
            "comparison_plan_id",
        ),
    ),

"""
    text = text.replace(
        "    _definition(\n"
        "        Intent.GET_PLAN_RENEWAL,\n"
        '        "get_plan_renewal",\n'
        "    ),\n\n"
        "    # Phase 1 — usage",
        "    _definition(\n"
        "        Intent.GET_PLAN_RENEWAL,\n"
        '        "get_plan_renewal",\n'
        "    ),\n"
        + insert
        + "\n    # Phase 1 — usage",
    )
    text = text.replace(
        "        optional=PERIOD,\n"
        "    ),\n"
        "    _definition(\n"
        "        Intent.GET_VOICE_USAGE,",
        "        optional=(\n            *PERIOD,\n            *PLAN_TYPE,\n        ),\n"
        "    ),\n"
        "    _definition(\n"
        "        Intent.GET_VOICE_USAGE,",
        1,
    )
    for intent_line, handler in (
        ("Intent.GET_VOICE_USAGE", "get_voice_usage"),
        ("Intent.GET_SMS_USAGE", "get_sms_usage"),
    ):
        text = text.replace(
            f"        {intent_line},\n"
            f'        "{handler}",\n'
            "        optional=PERIOD,\n",
            f"        {intent_line},\n"
            f'        "{handler}",\n'
            "        optional=(\n"
            "            *PERIOD,\n"
            "            *PLAN_TYPE,\n"
            "        ),\n",
            1,
        )
    text = text.replace(
        "        Intent.GET_DATA_USAGE,\n"
        '        "get_data_usage",\n'
        "        optional=PERIOD,\n",
        "        Intent.GET_DATA_USAGE,\n"
        '        "get_data_usage",\n'
        "        optional=(\n"
        "            *PERIOD,\n"
        "            *PLAN_TYPE,\n"
        "        ),\n",
    )
    replacements = [
        (
            "        optional=(\n"
            "            \"usage_type\",\n"
            "        ),\n"
            "        optional=PERIOD,\n",
            "        optional=(\n"
            "            \"usage_type\",\n"
            "            *PERIOD,\n"
            "            *PLAN_TYPE,\n"
            "        ),\n",
        ),
        (
            "        optional=(\n"
            "            \"usage_type\",\n"
            "        ),\n"
            "        optional=(\n"
            "            \"percentage_type\",\n"
            "            *PERIOD,\n"
            "        ),\n",
            "        optional=(\n"
            "            \"usage_type\",\n"
            "            \"percentage_type\",\n"
            "            *PERIOD,\n"
            "            *PLAN_TYPE,\n"
            "        ),\n",
        ),
        (
            "        Intent.GET_USAGE_SUMMARY,\n"
            '        "get_usage_summary",\n'
            "        optional=PERIOD,\n",
            "        Intent.GET_USAGE_SUMMARY,\n"
            '        "get_usage_summary",\n'
            "        optional=(\n"
            "            *PERIOD,\n"
            "            *PLAN_TYPE,\n"
            "        ),\n",
        ),
        (
            "        optional=(\n"
            "            \"month_count\",\n"
            "        ),\n"
            "    ),\n"
            "    _definition(\n"
            "        Intent.GET_USAGE_COMPARISON,",
            "        optional=(\n"
            "            \"month_count\",\n"
            "            *PLAN_TYPE,\n"
            "        ),\n"
            "    ),\n"
            "    _definition(\n"
            "        Intent.GET_USAGE_COMPARISON,",
        ),
    ]
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new, 1)

    billing_insert = """
    _definition(
        Intent.GET_BILL_CHARGE_SUMMARY,
        "get_bill_charge_summary",
        required=("bill_item_type",),
        optional=("month_count", *PLAN_TYPE),
    ),
    _definition(
        Intent.GET_PROJECTED_BILL,
        "get_projected_bill",
        optional=PLAN_TYPE,
    ),

"""
    text = text.replace(
        "        ),\n"
        "    ),\n\n"
        "    # Phase 3 — payments",
        "        ),\n"
        "    ),\n"
        + billing_insert
        + "\n    # Phase 3 — payments",
        1,
    )
    text = text.replace(
        "            \"limit\",\n"
        "        ),\n"
        "    ),\n\n"
        "    # Phase 3 — payments",
        "            \"limit\",\n"
        "            *PLAN_TYPE,\n"
        "        ),\n"
        "    ),\n\n"
        "    # Phase 3 — payments",
        1,
    )
    pay_insert = """
    _definition(
        Intent.GET_PAYMENT_PROFILE,
        "get_payment_profile_status",
    ),
    _definition(
        Intent.GET_ACCOUNT_CREDITS,
        "get_account_credits",
    ),

"""
    text = text.replace(
        "    ),\n\n"
        "    # Phase 4 — support",
        pay_insert
        + "\n    # Phase 4 — support",
        1,
    )
    path.write_text(text, encoding="utf-8")


def patch_router() -> None:
    path = ROOT / "app/intent/router.py"
    text = path.read_text(encoding="utf-8")
    if "get_list_subscriptions" in text:
        return
    text = text.replace(
        "from app.handlers.plans import (\n"
        "    get_current_plan,\n"
        "    get_plan_renewal,\n"
        ")\n",
        "from app.handlers.plans import (\n"
        "    get_current_plan,\n"
        "    get_plan_renewal,\n"
        ")\n"
        "from app.handlers.subscriptions_catalog import (\n"
        "    get_list_subscriptions,\n"
        "    get_plan_catalog,\n"
        "    get_plan_comparison,\n"
        ")\n"
        "from app.handlers.billing_extras import (\n"
        "    get_bill_charge_summary,\n"
        "    get_projected_bill,\n"
        ")\n"
        "from app.handlers.payment_profile import (\n"
        "    get_account_credits,\n"
        "    get_payment_profile_status,\n"
        ")\n",
    )
    text = text.replace(
        '    "get_plan_renewal": get_plan_renewal,\n\n'
        "    # Phase 1",
        '    "get_plan_renewal": get_plan_renewal,\n'
        '    "get_list_subscriptions": get_list_subscriptions,\n'
        '    "get_plan_catalog": get_plan_catalog,\n'
        '    "get_plan_comparison": get_plan_comparison,\n\n'
        "    # Phase 1",
    )
    text = text.replace(
        '    "filter_bills": filter_bills,\n\n'
        "    # Phase 3",
        '    "filter_bills": filter_bills,\n'
        '    "get_bill_charge_summary": get_bill_charge_summary,\n'
        '    "get_projected_bill": get_projected_bill,\n\n'
        "    # Phase 3",
    )
    text = text.replace(
        '    "get_payment_aggregate": get_payment_aggregate,\n\n'
        "    # Phase 4",
        '    "get_payment_aggregate": get_payment_aggregate,\n'
        '    "get_payment_profile_status": get_payment_profile_status,\n'
        '    "get_account_credits": get_account_credits,\n\n'
        "    # Phase 4",
    )
    path.write_text(text, encoding="utf-8")


def patch_customers_query() -> None:
    path = ROOT / "app/database/queries/customers.py"
    path.write_text(
        '''"""Customer database queries for NexaTel."""

from __future__ import annotations

import sqlite3


def get_customer(
    db: sqlite3.Connection,
    customer_id: str,
) -> sqlite3.Row | None:
    """Return one customer by customer ID."""

    cursor = db.execute(
        """
        SELECT
            customer_id,
            name,
            email,
            phone_number AS phone,
            city,
            service_address_line,
            service_state,
            service_postal_code,
            account_status,
            registration_date AS created_at
        FROM customers
        WHERE customer_id = ?
        """,
        (customer_id,),
    )

    return cursor.fetchone()
''',
        encoding="utf-8",
    )


def patch_account_handler() -> None:
    path = ROOT / "app/handlers/account.py"
    text = path.read_text(encoding="utf-8")
    if "service_address_line" in text:
        return
    text = text.replace(
        '        "city": row["city"],\n',
        '        "city": row["city"],\n'
        '        "service_address_line": row["service_address_line"],\n'
        '        "service_state": row["service_state"],\n'
        '        "service_postal_code": row["service_postal_code"],\n',
    )
    path.write_text(text, encoding="utf-8")


def patch_support_ticket_dict() -> None:
    path = ROOT / "app/handlers/support.py"
    text = path.read_text(encoding="utf-8")
    if "related_bill_id" in text:
        return
    text = text.replace(
        '        "updated_at": ticket[\n'
        '            "updated_at"\n'
        "        ],\n"
        '        "is_unresolved": (',
        '        "updated_at": ticket[\n'
        '            "updated_at"\n'
        "        ],\n"
        '        "related_bill_id": ticket[\n'
        '            "related_bill_id"\n'
        "        ] if \"related_bill_id\" in ticket.keys() else None,\n"
        '        "related_payment_id": ticket[\n'
        '            "related_payment_id"\n'
        "        ] if \"related_payment_id\" in ticket.keys() else None,\n"
        '        "is_unresolved": (',
    )
    path.write_text(text, encoding="utf-8")


def patch_response_service() -> None:
    path = ROOT / "app/services/response_service.py"
    text = path.read_text(encoding="utf-8")
    if "SUBSCRIPTION_LIST" in text:
        return
    formatters = '''
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
    marker = "RESULT_FORMATTERS = {"
    text = text.replace(marker, formatters + "\n" + marker)
    text = text.replace(
        '    "BILL_CHANGE_INSUFFICIENT_DETAIL": (',
        '    "SUBSCRIPTION_LIST": _format_subscription_list,\n'
        '    "PLAN_CATALOG": _format_plan_catalog,\n'
        '    "PLAN_COMPARISON": _format_plan_comparison,\n'
        '    "BILL_CHARGE_SUMMARY": _format_bill_charge_summary,\n'
        '    "PROJECTED_BILL": _format_projected_bill,\n'
        '    "PAYMENT_PROFILE": _format_payment_profile,\n'
        '    "ACCOUNT_CREDITS": _format_account_credits,\n'
        '    "BILL_CHANGE_INSUFFICIENT_DETAIL": (',
    )
    path.write_text(text, encoding="utf-8")


def patch_seed() -> None:
    path = ROOT / "app/database/seed.py"
    text = path.read_text(encoding="utf-8")
    if "_customer_extensions" in text:
        return
    text = text.replace(
        '"INSERT INTO customers VALUES (?,?,?,?,?,?,?)",',
        '"INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?,?)",',
    )
    text = text.replace(
        "        CUSTOMERS,\n"
        "    )\n\n"
        "    connection.executemany(\n"
        '        """\n'
        "        INSERT INTO plans (",
        "        _customers(),\n"
        "    )\n\n"
        "    connection.executemany(\n"
        '        """\n'
        "        INSERT INTO plans (",
    )

    ext_fn = '''

def _customers() -> list[tuple]:
    rows = []
    for customer in CUSTOMERS:
        rows.append(
            (
                *customer,
                "",
                "",
                "",
            )
        )
    rows[2] = (
        "CUST003",
        "Rohan Kapoor",
        "rohan.kapoor@example.com",
        "+919000000003",
        "Bengaluru",
        "42 MG Road, Indiranagar",
        "Karnataka",
        "560038",
        "ACTIVE",
        "2023-11-10",
    )
    return rows


def _customer_extensions(connection: sqlite3.Connection) -> None:
    profiles = [
        ("CUST001", 1, "UPI", "UPI •••• 1234"),
        ("CUST002", 0, "CREDIT_CARD", "Visa ending 4242"),
        ("CUST003", 1, "NET_BANKING", "HDFC NetBanking"),
        ("CUST005", 1, "DEBIT_CARD", "Debit ending 9911"),
    ]
    connection.executemany(
        """
        INSERT INTO customer_payment_profiles
        VALUES (?,?,?,?)
        """,
        profiles,
    )
    credits = [
        (
            "CRD001",
            "CUST002",
            150.0,
            "Goodwill credit for roaming confusion",
            "2026-09-20",
            "AVAILABLE",
        ),
    ]
    connection.executemany(
        """
        INSERT INTO account_credits
        VALUES (?,?,?,?,?,?)
        """,
        credits,
    )

'''
    text = text.replace(
        "def _id(prefix: str, number: int) -> str:",
        ext_fn + "\ndef _id(prefix: str, number: int) -> str:",
    )
    text = text.replace(
        "    _devices(connection)\n",
        "    _devices(connection)\n"
        "    _customer_extensions(connection)\n",
    )
    text = text.replace(
        "        INSERT INTO support_tickets\n"
        "        VALUES (?,?,?,?,?,?,?,?)\n",
        "        INSERT INTO support_tickets\n"
        "        VALUES (?,?,?,?,?,?,?,?,?,?)\n",
    )
    text = text.replace(
        "            rows.append(\n"
        "                (\n"
        "                    _id(\"TKT\", ticket_number),\n"
        "                    customer[0],\n"
        "                    *entry,\n"
        "                )\n"
        "            )",
        "            related_bill = None\n"
        "            related_payment = None\n"
        "            if (\n"
        "                customer_index == 2\n"
        "                and entry[0] == \"BILLING\"\n"
        "            ):\n"
        "                related_bill = \"BILL027\"\n"
        "            rows.append(\n"
        "                (\n"
        "                    _id(\"TKT\", ticket_number),\n"
        "                    customer[0],\n"
        "                    *entry,\n"
        "                    related_bill,\n"
        "                    related_payment,\n"
        "                )\n"
        "            )",
    )
    tables = '"customers",\n    ]'
    text = text.replace(
        tables,
        '"customer_payment_profiles",\n'
        '        "account_credits",\n'
        '        "customers",\n'
        "    ]",
    )
    path.write_text(text, encoding="utf-8")


def patch_llm_client() -> None:
    path = ROOT / "app/llm/client.py"
    text = path.read_text(encoding="utf-8")
    if "_classify_billing_service_request" in text:
        return
    snippet = '''

def _classify_billing_service_request(
    text: str,
) -> LLMIntentResponse | None:
    if "bill" not in text and "owe" not in text:
        return None
    if any(
        term in text
        for term in (
            "phone bill",
            "mobile bill",
            "fiber bill",
            "broadband bill",
        )
    ):
        parameters = IntentParameters()
        if "fiber" in text or "broadband" in text:
            parameters.plan_type = PlanType.FIBER
        else:
            parameters.plan_type = PlanType.MOBILE
        return LLMIntentResponse(
            intent=Intent.GET_CURRENT_BILL,
            parameters=parameters,
        )
    return None


def _classify_subscription_inventory(
    text: str,
) -> LLMIntentResponse | None:
    if any(
        phrase in text
        for phrase in (
            "what services",
            "my services",
            "list subscriptions",
            "how many subscriptions",
            "mobile and fiber",
        )
    ):
        return LLMIntentResponse(
            intent=Intent.GET_LIST_SUBSCRIPTIONS,
        )
    return None

'''
    text = text.replace(
        "def classify_deterministic_request(",
        snippet + "\ndef classify_deterministic_request(",
    )
    text = text.replace(
        "    payment_help = _classify_general_payment_help(\n"
        "        text\n"
        "    )\n\n"
        "    if payment_help is not None:\n"
        "        return payment_help\n",
        "    payment_help = _classify_general_payment_help(\n"
        "        text\n"
        "    )\n\n"
        "    if payment_help is not None:\n"
        "        return payment_help\n\n"
        "    billing_service = _classify_billing_service_request(\n"
        "        text\n"
        "    )\n\n"
        "    if billing_service is not None:\n"
        "        return billing_service\n\n"
        "    subscription_inventory = _classify_subscription_inventory(\n"
        "        text\n"
        "    )\n\n"
        "    if subscription_inventory is not None:\n"
        "        return subscription_inventory\n",
    )
    if "PlanType" not in text.split("def classify_deterministic_request")[0]:
        text = text.replace(
            "from app.models.domain import (\n",
            "from app.models.domain import (\n    PlanType,\n",
            1,
        )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    patch_parameters()
    patch_definitions()
    patch_router()
    patch_customers_query()
    patch_account_handler()
    patch_support_ticket_dict()
    patch_response_service()
    patch_seed()
    patch_llm_client()
    print("wiring patched")


if __name__ == "__main__":
    main()
