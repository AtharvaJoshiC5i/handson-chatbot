"""Read-only account snapshot for the chat UI."""

from __future__ import annotations

from datetime import datetime, timezone
import sqlite3

from app.business.dates import resolve_usage_period
from app.database.queries.bills import get_current_statement_bill
from app.database.queries.credits import get_available_credit_total
from app.database.queries.customers import get_customer
from app.database.queries.payment_profiles import get_payment_profile
from app.database.queries.payments import get_latest_payment
from app.database.queries.subscriptions import (
    get_usage_plan_for_customer,
    list_subscriptions_for_customer,
)
from app.database.queries.usage import get_usage_totals_by_date_range
from app.handlers.billing_extras import get_projected_bill
from app.handlers.cross_domain import get_account_attention_summary
from app.models.domain import CustomerContext, TimeRange, TruthStatus


def _mask_phone(phone: str) -> str:
    digits = phone.strip()
    if len(digits) < 4:
        return digits
    return f"{digits[:-4]}****"


def build_account_snapshot(
    db: sqlite3.Connection,
    customer_id: str,
) -> dict | None:
    customer = get_customer(db, customer_id)
    if customer is None:
        return None

    subscriptions = list_subscriptions_for_customer(
        db,
        customer_id,
    )
    active_subs = [
        {
            "subscription_id": row["subscription_id"],
            "plan_name": row["plan_name"],
            "plan_type": row["plan_type"],
            "status": row["status"],
            "renewal_date": row["renewal_date"],
            "monthly_price": float(row["monthly_price"]),
        }
        for row in subscriptions
        if row["status"] == "ACTIVE"
    ]

    plan_row = get_usage_plan_for_customer(
        db,
        customer_id,
    )
    plan = None
    usage_headline = None

    if plan_row is not None:
        plan = {
            "plan_name": plan_row["plan_name"],
            "plan_type": plan_row["plan_type"],
            "renewal_date": plan_row["renewal_date"],
            "data_limit_gb": float(plan_row["data_limit_gb"]),
            "is_data_unlimited": bool(
                plan_row["is_data_unlimited"]
            ),
        }

        try:
            period = resolve_usage_period(
                time_range=TimeRange.CURRENT_MONTH,
                month=None,
                year=None,
            )
            totals = get_usage_totals_by_date_range(
                db,
                customer_id,
                period.start_date.isoformat(),
                period.end_date.isoformat(),
                subscription_id=plan_row["subscription_id"],
            )
            if int(totals["record_count"]) > 0:
                used = float(totals["data_used_gb"])
                if plan["is_data_unlimited"]:
                    usage_headline = (
                        f"{used:.1f} GB used this month"
                    )
                elif plan["data_limit_gb"] > 0:
                    pct = min(
                        999.0,
                        round(
                            100.0
                            * used
                            / plan["data_limit_gb"],
                            1,
                        ),
                    )
                    usage_headline = (
                        f"{used:.1f} / "
                        f"{plan['data_limit_gb']:.0f} GB "
                        f"({pct}%)"
                    )
        except ValueError:
            pass

    bill_row = get_current_statement_bill(
        db,
        customer_id,
    )
    bill = None
    if bill_row is not None:
        bill = {
            "bill_id": bill_row["bill_id"],
            "amount": float(bill_row["amount"]),
            "due_date": bill_row["due_date"],
            "status": bill_row["status"],
            "plan_type": bill_row["plan_type"],
        }

    bills_by_line: list[dict] = []
    if len(active_subs) > 1:
        for sub in active_subs:
            line_bill = get_current_statement_bill(
                db,
                customer_id,
                plan_type=sub["plan_type"],
            )
            if line_bill is None:
                continue
            bills_by_line.append(
                {
                    "plan_type": sub["plan_type"],
                    "plan_name": sub["plan_name"],
                    "bill_id": line_bill["bill_id"],
                    "amount": float(line_bill["amount"]),
                    "due_date": line_bill["due_date"],
                    "status": line_bill["status"],
                }
            )

    payment_row = get_latest_payment(
        db,
        customer_id,
    )
    payment = None
    if payment_row is not None:
        payment = {
            "status": payment_row["status"],
            "failure_reason": payment_row["failure_reason"]
            if "failure_reason" in payment_row.keys()
            else None,
        }

    profile_row = get_payment_profile(
        db,
        customer_id,
    )
    has_payment_profile = profile_row is not None
    payment_profile = None
    if profile_row is not None:
        payment_profile = {
            "autopay_enabled": bool(
                profile_row["autopay_enabled"]
            ),
            "payment_method_label": profile_row[
                "payment_method_label"
            ],
        }

    credits_total = get_available_credit_total(
        db,
        customer_id,
    )

    attention_result = get_account_attention_summary(
        db,
        CustomerContext(customer_id=customer_id),
    )
    attention_items = []
    if (
        attention_result.status == TruthStatus.VERIFIED
        and attention_result.data is not None
    ):
        attention_items = attention_result.data.get(
            "items",
            [],
        )

    projected_bill = None
    projected_result = get_projected_bill(
        db,
        CustomerContext(customer_id=customer_id),
    )
    if (
        projected_result.status == TruthStatus.VERIFIED
        and projected_result.data is not None
    ):
        projected_bill = {
            "estimated_amount": float(
                projected_result.data["estimated_amount"]
            ),
            "plan_name": projected_result.data["plan_name"],
            "plan_type": projected_result.data["plan_type"],
            "as_of_date": projected_result.data["as_of_date"],
        }

    return {
        "customer_id": customer_id,
        "name": customer["name"],
        "phone_masked": _mask_phone(
            customer["phone"],
        ),
        "city": customer["city"],
        "service_address_line": customer[
            "service_address_line"
        ]
        if "service_address_line" in customer.keys()
        else "",
        "account_status": customer["account_status"],
        "plan": plan,
        "usage_headline": usage_headline,
        "bill": bill,
        "bills_by_line": bills_by_line,
        "payment": payment,
        "payment_profile": payment_profile,
        "has_payment_profile": has_payment_profile,
        "projected_bill": projected_bill,
        "available_credits": round(
            credits_total,
            2,
        ),
        "active_subscriptions": active_subs,
        "attention_items": attention_items,
        "generated_at": datetime.now(
            timezone.utc,
        ).isoformat(),
    }
