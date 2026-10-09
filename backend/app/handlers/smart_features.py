"""Smart bill anomaly detection and plan recommendation."""

from __future__ import annotations

import sqlite3
from statistics import mean

from app.database.queries.plans import list_plans
from app.database.queries.usage import get_monthly_usage_totals
from app.handlers.billing import explain_bill_change
from app.handlers.plans import get_current_plan
from app.models.domain import CustomerContext, TruthStatus
from app.truth.result import (
    TruthResult,
    verified_result,
)
from app.truth.sources import source_for_table


_ITEM_TYPE_LABELS = {
    "ROAMING": "roaming",
    "USAGE": "additional usage",
    "DATA": "data usage",
    "VOICE": "voice usage",
    "SMS": "SMS",
    "TAX": "taxes",
    "DISCOUNT": "discounts",
    "PLAN": "plan charges",
    "PLAN_CHARGE": "plan rental",
    "EQUIPMENT": "equipment",
    "DATA_ADDON": "data add-on",
    "OTHER": "other charges",
}


def _money(value: float) -> float:
    return round(float(value), 2)


def _item_label(
    item_type: str,
    descriptions: list[str] | None = None,
) -> str:
    key = str(item_type or "OTHER").upper()
    if descriptions:
        primary = str(descriptions[0]).strip()
        if primary:
            return primary
    return _ITEM_TYPE_LABELS.get(
        key,
        key.replace("_", " ").lower(),
    )


def _descriptions_from_item(
    item: dict,
    bucket: str,
) -> list[str]:
    if bucket == "added_items":
        return list(item.get("descriptions") or [])
    if bucket == "removed_items":
        return list(item.get("descriptions") or [])
    return list(
        item.get("current_descriptions")
        or item.get("descriptions")
        or []
    )


def _is_roaming_related_tax(
    item_type: str,
    descriptions: list[str],
) -> bool:
    if str(item_type).upper() != "TAX":
        return False
    blob = " ".join(descriptions).lower()
    return "roaming" in blob or "roam" in blob


def _collect_signed_deltas(
    data: dict,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for item in data.get("added_items", []):
        amount = float(item.get("amount", 0))
        if abs(amount) <= 0.01:
            continue
        item_type = str(item.get("item_type", "OTHER"))
        descriptions = _descriptions_from_item(
            item,
            "added_items",
        )
        rows.append(
            {
                "item_type": item_type,
                "descriptions": descriptions,
                "amount": _money(amount),
            }
        )

    for item in data.get("changed_items", []):
        amount = float(item.get("difference", 0))
        if abs(amount) <= 0.01:
            continue
        item_type = str(item.get("item_type", "OTHER"))
        descriptions = _descriptions_from_item(
            item,
            "changed_items",
        )
        rows.append(
            {
                "item_type": item_type,
                "descriptions": descriptions,
                "amount": _money(amount),
            }
        )

    for item in data.get("removed_items", []):
        amount = -float(item.get("amount", 0))
        if abs(amount) <= 0.01:
            continue
        item_type = str(item.get("item_type", "OTHER"))
        descriptions = _descriptions_from_item(
            item,
            "removed_items",
        )
        rows.append(
            {
                "item_type": item_type,
                "descriptions": descriptions,
                "amount": _money(amount),
            }
        )

    return rows


def _consolidate_breakdown(
    deltas: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Merge roaming-related tax into roaming; keep signed amounts."""

    roaming_amount = 0.0
    roaming_tax_amount = 0.0
    roaming_descriptions: list[str] = []
    other: list[dict[str, object]] = []

    for row in deltas:
        item_type = str(row["item_type"]).upper()
        amount = float(row["amount"])
        descriptions = list(row.get("descriptions") or [])

        if item_type == "ROAMING":
            roaming_amount += amount
            roaming_descriptions.extend(descriptions)
            continue

        if _is_roaming_related_tax(
            item_type,
            descriptions,
        ):
            roaming_tax_amount += amount
            continue

        other.append(
            {
                "item_type": item_type,
                "descriptions": descriptions,
                "amount": _money(amount),
            }
        )

    breakdown: list[dict[str, object]] = []

    if abs(roaming_amount) > 0.01 or abs(
        roaming_tax_amount
    ) > 0.01:
        total_roaming = _money(
            roaming_amount + roaming_tax_amount
        )
        if roaming_tax_amount > 0.01 and roaming_amount > 0:
            label = (
                "International roaming "
                f"(incl. ₹{_money(roaming_tax_amount)} tax)"
            )
        elif roaming_descriptions:
            label = _item_label(
                "ROAMING",
                roaming_descriptions,
            )
        else:
            label = "Roaming charges"

        breakdown.append(
            {
                "item_type": "ROAMING",
                "label": label,
                "amount": total_roaming,
            }
        )

    for row in other:
        item_type = str(row["item_type"])
        amount = float(row["amount"])
        descriptions = list(row.get("descriptions") or [])
        label = _item_label(
            item_type,
            descriptions,
        )
        if item_type.upper() == "PLAN_CHARGE" and amount < 0:
            label = "Lower plan rental vs previous month"
        elif item_type.upper() == "PLAN_CHARGE" and amount > 0:
            label = "Higher plan rental vs previous month"

        breakdown.append(
            {
                "item_type": item_type,
                "label": label,
                "amount": _money(amount),
            }
        )

    breakdown.sort(
        key=lambda row: abs(float(row["amount"])),
        reverse=True,
    )
    return breakdown


def _build_bill_increase_breakdown(
    data: dict,
    total_difference: float,
) -> list[dict[str, object]]:
    deltas = _collect_signed_deltas(data)
    breakdown = _consolidate_breakdown(deltas)

    explained = _money(
        sum(float(row["amount"]) for row in breakdown)
    )
    gap = _money(total_difference - explained)

    if abs(gap) > 0.01:
        breakdown.append(
            {
                "item_type": "OTHER",
                "label": "Other line-item adjustments",
                "amount": gap,
            }
        )

    return breakdown


def _main_positive_drivers(
    breakdown: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Largest positive contributors for short summaries."""

    positives = [
        row
        for row in breakdown
        if float(row["amount"]) > 0.01
    ]
    positives.sort(
        key=lambda row: float(row["amount"]),
        reverse=True,
    )
    return positives[:5]


def detect_bill_anomaly(
    db: sqlite3.Connection,
    customer: CustomerContext,
    **kwargs,
) -> TruthResult[dict]:
    """Explain an unusually high bill vs the previous period."""

    base = explain_bill_change(
        db,
        customer,
        **kwargs,
    )

    if base.status != TruthStatus.VERIFIED:
        return base

    data = base.data or {}
    if data.get("result_type") == "BILL_CHANGE_INSUFFICIENT_DETAIL":
        current = data.get("current_bill")
        previous = data.get("comparison_bill")
        if not current or not previous:
            return base
        difference = float(data.get("total_difference", 0))
        return verified_result(
            {
                "result_type": "BILL_ANOMALY_DETECTION",
                "current_bill": current,
                "comparison_bill": previous,
                "total_difference": _money(difference),
                "percent_increase": None,
                "is_unusual_increase": difference > 0,
                "breakdown_lines": [],
                "main_drivers": [],
                "direction": data.get("direction", "INCREASE"),
                "comparison_scope": (
                    f"{current.get('period')} vs "
                    f"{previous.get('period')}"
                ),
            },
            source=source_for_table("bill_items"),
        )

    current = data.get("current_bill")
    previous = data.get("comparison_bill")

    if not current or not previous:
        return base

    current_amount = float(current["amount"])
    previous_amount = float(previous["amount"])
    difference = float(
        data.get(
            "total_difference",
            current_amount - previous_amount,
        )
    )

    percent_change = None
    if previous_amount > 0 and difference > 0:
        percent_change = round(
            100.0 * difference / previous_amount,
            1,
        )

    breakdown = _build_bill_increase_breakdown(
        data,
        difference,
    )
    drivers = _main_positive_drivers(breakdown)
    is_unusual = (
        difference > 0
        and (
            percent_change is not None
            and percent_change >= 10.0
            or difference >= 200
        )
    )

    return verified_result(
        {
            "result_type": "BILL_ANOMALY_DETECTION",
            "current_bill": current,
            "comparison_bill": previous,
            "total_difference": _money(difference),
            "percent_increase": percent_change,
            "is_unusual_increase": is_unusual,
            "breakdown_lines": breakdown,
            "main_drivers": drivers,
            "direction": data.get("direction", "INCREASE"),
            "comparison_scope": (
                f"{current.get('period')} vs "
                f"{previous.get('period')}"
            ),
        },
        source=source_for_table("bill_items"),
    )


def _inr(value: float) -> str:
    amount = _money(value)
    if abs(amount - round(amount)) < 0.01:
        return f"₹{int(round(amount))}"
    return f"₹{amount:g}"


def _usage_fit_summary(
    *,
    avg_gb: float,
    months_sampled: int,
    current_limit: float,
) -> dict[str, object]:
    utilization = None
    unused = None
    if current_limit > 0:
        utilization = round(
            100.0 * avg_gb / current_limit,
            1,
        )
        unused = round(
            max(0.0, current_limit - avg_gb),
            1,
        )

    return {
        "average_monthly_data_gb": avg_gb,
        "months_sampled": months_sampled,
        "current_data_allowance_gb": (
            current_limit if current_limit > 0 else None
        ),
        "utilization_percent": utilization,
        "typical_unused_data_gb": unused,
    }


def _build_plan_recommendation_reasons(
    *,
    status: str,
    current_name: str,
    current_price: float,
    current_limit: float,
    avg_gb: float,
    months_sampled: int,
    needed_gb: float,
    buffer_gb: float,
    recommended: dict | None,
    savings: float,
) -> list[str]:
    month_label = (
        f"the last {months_sampled} months"
        if months_sampled != 1
        else "the last month"
    )
    reasons = [
        (
            f"You use about {avg_gb:g} GB of data per month on average "
            f"({month_label})."
        ),
    ]

    if current_limit > 0:
        unused = max(0.0, current_limit - avg_gb)
        reasons.append(
            f"{current_name} includes {current_limit:g} GB per month, "
            f"so you often have about {unused:g} GB left unused."
        )

    if status == "KEEP_CURRENT":
        reasons.append(
            "Your recent usage fits your current allowance well, so "
            "switching plans is unlikely to save money or improve coverage."
        )
        return reasons

    if status in ("NO_ALTERNATIVES", "INSUFFICIENT_USAGE"):
        return reasons

    if not recommended:
        return reasons

    rec_name = str(recommended.get("plan_name", "the suggested plan"))
    rec_limit = float(recommended.get("data_limit_gb") or 0)
    rec_price = float(recommended.get("monthly_price") or 0)
    headroom = (
        round(max(0.0, rec_limit - avg_gb), 1)
        if rec_limit > 0
        else None
    )

    if rec_limit > 0 and rec_limit >= needed_gb and headroom is not None:
        reasons.append(
            f"{rec_name} includes {rec_limit:g} GB, which still covers "
            f"your typical usage with about {headroom:g} GB of headroom "
            f"(we allow roughly {buffer_gb:g} GB above your average)."
        )
    elif rec_limit > 0:
        reasons.append(
            f"{rec_name} includes {rec_limit:g} GB, the best match in "
            f"our catalog for how you use data today."
        )

    if savings > 0:
        reasons.append(
            f"Monthly cost would drop from {_inr(current_price)} on "
            f"{current_name} to {_inr(rec_price)} on {rec_name} — about "
            f"{_inr(savings)} less per month."
        )
    elif rec_price < current_price:
        reasons.append(
            f"{rec_name} costs less than {current_name} while still "
            f"supporting your recent usage."
        )
    elif status == "DOWNGRADE_OPTION":
        reasons.append(
            "You would pay for less unused data allowance than on your "
            "current plan."
        )

    return reasons


def recommend_plan_for_customer(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    plan_type: str | None = None,
) -> TruthResult[dict]:
    """Recommend a mobile/fiber plan from catalog based on recent usage."""

    current_result = get_current_plan(
        db,
        customer,
        plan_type=plan_type,
    )

    if current_result.status != TruthStatus.VERIFIED:
        return current_result

    current = current_result.data or {}
    if current.get("is_data_unlimited"):
        plan_name = str(current.get("plan_name", "your plan"))
        return verified_result(
            {
                "result_type": "PLAN_RECOMMENDATION",
                "recommendation_status": "ALREADY_OPTIMAL",
                "current_plan": current,
                "message_key": "unlimited",
                "recommendation_reasons": [
                    (
                        f"{plan_name} already includes unlimited data, "
                        "so there is no smaller allowance plan to move to."
                    ),
                ],
            },
            source=source_for_table("plans"),
        )

    subscription_id = current.get("subscription_id")
    monthly_rows = get_monthly_usage_totals(
        db,
        customer.customer_id,
        subscription_id=subscription_id,
    )

    completed_months = [
        row
        for row in monthly_rows
        if int(row["record_count"]) > 0
    ][-3:]

    if not completed_months:
        return verified_result(
            {
                "result_type": "PLAN_RECOMMENDATION",
                "recommendation_status": "INSUFFICIENT_USAGE",
                "current_plan": current,
                "recommendation_reasons": [
                    (
                        "We need at least one completed month of "
                        "usage on your line before comparing plans."
                    ),
                ],
            },
            source=source_for_table("usage"),
        )

    avg_gb = mean(
        float(row["data_used_gb"])
        for row in completed_months
    )
    avg_gb = round(avg_gb, 1)

    target_plan_type = current.get("plan_type", "MOBILE")
    catalog = list_plans(
        db,
        plan_type=target_plan_type,
    )

    mobile_catalog = [
        row
        for row in catalog
        if not bool(row["is_data_unlimited"])
    ]

    if not mobile_catalog:
        return verified_result(
            {
                "result_type": "PLAN_RECOMMENDATION",
                "recommendation_status": "NO_ALTERNATIVES",
                "current_plan": current,
                "average_monthly_data_gb": avg_gb,
                "recommendation_reasons": [
                    (
                        "No other catalog plans are available to compare "
                        "with your current subscription."
                    ),
                ],
            },
            source=source_for_table("plans"),
        )

    current_price = float(current["monthly_price"])
    current_limit = float(current.get("data_limit_gb") or 0)
    buffer_gb = max(5.0, avg_gb * 0.25)
    needed_gb = avg_gb + buffer_gb

    candidates = [
        row
        for row in mobile_catalog
        if float(row["data_limit_gb"]) >= needed_gb
    ]

    if not candidates:
        candidates = mobile_catalog

    recommended = min(
        candidates,
        key=lambda row: (
            float(row["monthly_price"]),
            float(row["data_limit_gb"]),
        ),
    )

    recommended_price = float(
        recommended["monthly_price"]
    )
    savings = _money(
        max(0.0, current_price - recommended_price)
    )

    same_plan = (
        recommended["plan_id"] == current.get("plan_id")
    )

    if same_plan and avg_gb < current_limit * 0.6:
        cheaper = [
            row
            for row in mobile_catalog
            if float(row["data_limit_gb"]) >= needed_gb
            and float(row["monthly_price"]) < current_price
        ]
        if cheaper:
            recommended = min(
                cheaper,
                key=lambda row: float(row["monthly_price"]),
            )
            recommended_price = float(
                recommended["monthly_price"]
            )
            savings = _money(
                current_price - recommended_price
            )
            same_plan = False

    status = "KEEP_CURRENT"
    if not same_plan and savings > 0:
        status = "SWITCH_RECOMMENDED"
    elif not same_plan and float(
        recommended["data_limit_gb"]
    ) < current_limit:
        status = "DOWNGRADE_OPTION"
    elif same_plan:
        status = "KEEP_CURRENT"

    months_sampled = len(completed_months)
    recommended_plan = {
        "plan_id": recommended["plan_id"],
        "plan_name": recommended["plan_name"],
        "monthly_price": _money(
            recommended_price
        ),
        "data_limit_gb": float(
            recommended["data_limit_gb"]
        ),
        "plan_type": recommended["plan_type"],
    }
    usage_fit = _usage_fit_summary(
        avg_gb=avg_gb,
        months_sampled=months_sampled,
        current_limit=current_limit,
    )
    reasons = _build_plan_recommendation_reasons(
        status=status,
        current_name=str(current.get("plan_name", "your plan")),
        current_price=current_price,
        current_limit=current_limit,
        avg_gb=avg_gb,
        months_sampled=months_sampled,
        needed_gb=needed_gb,
        buffer_gb=buffer_gb,
        recommended=(
            recommended_plan
            if status != "KEEP_CURRENT"
            else None
        ),
        savings=float(savings),
    )

    return verified_result(
        {
            "result_type": "PLAN_RECOMMENDATION",
            "recommendation_status": status,
            "current_plan": current,
            "average_monthly_data_gb": avg_gb,
            "recommended_plan": (
                recommended_plan
                if status != "KEEP_CURRENT"
                else None
            ),
            "estimated_monthly_savings": (
                savings if status != "KEEP_CURRENT" else 0.0
            ),
            "months_sampled": months_sampled,
            "usage_fit": usage_fit,
            "recommendation_reasons": reasons,
        },
        source=source_for_table("plans"),
    )
