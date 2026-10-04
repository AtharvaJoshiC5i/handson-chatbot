"""One-off patch helper for structured gap implementation."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch_domain() -> None:
    path = ROOT / "app" / "models" / "domain.py"
    text = path.read_text(encoding="utf-8")
    if "GET_LIST_SUBSCRIPTIONS" in text:
        return
    text = text.replace(
        '    GET_PLAN_RENEWAL = "GET_PLAN_RENEWAL"\n',
        (
            '    GET_PLAN_RENEWAL = "GET_PLAN_RENEWAL"\n'
            '    GET_LIST_SUBSCRIPTIONS = "GET_LIST_SUBSCRIPTIONS"\n'
            '    GET_PLAN_CATALOG = "GET_PLAN_CATALOG"\n'
            '    GET_PLAN_COMPARISON = "GET_PLAN_COMPARISON"\n'
        ),
    )
    text = text.replace(
        '    FILTER_BILLS = "FILTER_BILLS"\n\n    # Phase 3 — payments',
        (
            '    FILTER_BILLS = "FILTER_BILLS"\n'
            '    GET_BILL_CHARGE_SUMMARY = "GET_BILL_CHARGE_SUMMARY"\n'
            '    GET_PROJECTED_BILL = "GET_PROJECTED_BILL"\n\n'
            '    # Phase 3 — payments'
        ),
    )
    text = text.replace(
        '    GET_PAYMENT_AGGREGATE = "GET_PAYMENT_AGGREGATE"\n\n    # Phase 4 — support',
        (
            '    GET_PAYMENT_AGGREGATE = "GET_PAYMENT_AGGREGATE"\n'
            '    GET_PAYMENT_PROFILE = "GET_PAYMENT_PROFILE"\n'
            '    GET_ACCOUNT_CREDITS = "GET_ACCOUNT_CREDITS"\n\n'
            '    # Phase 4 — support'
        ),
    )
    if "class BillItemType" not in text:
        text = text.replace(
            "class BillSortOrder(str, Enum):",
            (
                "class BillItemType(str, Enum):\n"
                '    PLAN_CHARGE = "PLAN_CHARGE"\n'
                '    ROAMING = "ROAMING"\n'
                '    DATA_ADDON = "DATA_ADDON"\n'
                '    TAX = "TAX"\n'
                '    OTHER = "OTHER"\n\n\n'
                "class BillSortOrder(str, Enum):"
            ),
        )
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_domain()
    print("patched domain")
