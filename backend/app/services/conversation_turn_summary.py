"""Compact verified summaries for conversation turn history."""

from __future__ import annotations

from typing import Any

from app.models.domain import TruthStatus
from app.truth.result import TruthResult

MAX_USER_MESSAGE_CHARS = 400
MAX_FACTS_CHARS = 180


def _truncate(text: str, limit: int) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def _money(value: Any) -> str:
    if value is None:
        return ""
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(amount - round(amount)) < 0.01:
        return f"₹{int(round(amount))}"
    return f"₹{amount:g}"


def _bill_line(bill: dict[str, Any]) -> str:
    period = bill.get("period") or bill.get("billing_period_start") or ""
    amount = _money(bill.get("amount"))
    status = bill.get("status") or ""
    bill_id = bill.get("bill_id") or ""
    parts = [str(period).strip(), amount]
    if status:
        parts.append(str(status))
    if bill_id:
        parts.append(bill_id)
    return " ".join(part for part in parts if part)


def _summarize_verified_data(data: dict[str, Any]) -> str:
    result_type = data.get("result_type") or ""

    if result_type == "BILL_COMPARISON":
        current = data.get("current_bill") or {}
        previous = data.get("comparison_bill") or {}
        return (
            f"compare {_bill_line(previous)} vs {_bill_line(current)}"
        )

    if result_type in {
        "BILL_CURRENT",
        "BILL_SPECIFIC",
        "BILL_BREAKDOWN",
    }:
        bill = data.get("bill") or data.get("current_bill") or data
        return _bill_line(bill) if isinstance(bill, dict) else result_type

    if result_type == "BILL_HISTORY":
        bills = data.get("bills") or []
        if bills:
            first = bills[0]
            last = bills[-1]
            return (
                f"{len(bills)} bills "
                f"{_bill_line(last)} … {_bill_line(first)}"
            )
        return "bill history empty"

    if result_type == "BILL_FILTER":
        bills = data.get("bills") or []
        if not bills:
            return "no matching bills"
        return f"{len(bills)} bills; latest {_bill_line(bills[0])}"

    if result_type == "BILL_ANOMALY_DETECTION":
        current = data.get("current_bill") or {}
        previous = data.get("comparison_bill") or {}
        diff = data.get("total_difference")
        return (
            f"anomaly {_bill_line(previous)} → {_bill_line(current)} "
            f"Δ{_money(diff)}"
        )

    if result_type == "USAGE_COMPARISON":
        return (
            f"{data.get('period_2', '')} vs {data.get('period_1', '')} "
            f"{data.get('period_2_usage')} vs {data.get('period_1_usage')} "
            f"{data.get('unit', '')}"
        ).strip()

    if result_type in {"USAGE_HISTORY", "USAGE_TREND"}:
        history = data.get("history") or []
        if history:
            latest = history[-1]
            return (
                f"{len(history)} months; latest "
                f"{latest.get('period')} {latest.get('value')} "
                f"{latest.get('unit', '')}"
            )
        return result_type

    if result_type.startswith("USAGE_") or result_type in {
        "DATA_USAGE",
        "VOICE_USAGE",
        "SMS_USAGE",
    }:
        period = data.get("period") or ""
        value = data.get("value") or data.get("used") or data.get("amount")
        unit = data.get("unit") or ""
        return f"{period} {value} {unit}".strip()

    if result_type == "PAYMENT_HISTORY":
        payments = data.get("payments") or []
        if payments:
            p = payments[0]
            return (
                f"{len(payments)} payments; latest "
                f"{_money(p.get('amount'))} {p.get('status', '')}"
            )
        return "payment history empty"

    if result_type in {
        "PAYMENT_STATUS",
        "PAYMENT_LATEST",
        "CROSS_BILL_PAYMENT_STATUS",
    }:
        payment = data.get("payment") or {}
        bill = data.get("bill") or data.get("current_bill") or {}
        parts = []
        if isinstance(bill, dict) and bill.get("period"):
            parts.append(_bill_line(bill))
        if isinstance(payment, dict) and payment:
            parts.append(
                f"payment {_money(payment.get('amount'))} "
                f"{payment.get('status', '')}"
            )
        return "; ".join(parts) or result_type

    if result_type == "DEVICE_LIST":
        devices = data.get("devices") or []
        if not devices:
            return "no devices"
        names = [
            f"{d.get('device_name', '')} ({d.get('device_type', '')})"
            for d in devices[:3]
            if isinstance(d, dict)
        ]
        extra = f" +{len(devices) - 3}" if len(devices) > 3 else ""
        return f"{len(devices)} devices: {', '.join(names)}{extra}"

    if result_type == "PLAN_COMPARISON":
        left = data.get("current") or {}
        right = data.get("previous") or {}
        return (
            f"{left.get('plan_id')} vs {right.get('plan_id')} "
            f"{_money(left.get('monthly_price'))} vs "
            f"{_money(right.get('monthly_price'))}"
        )

    if result_type in {"SUPPORT_HISTORY", "SUPPORT_FILTER"}:
        tickets = data.get("tickets") or []
        if tickets:
            t = tickets[0]
            return (
                f"{len(tickets)} tickets; "
                f"{t.get('ticket_id')} {t.get('status', '')}"
            )
        return "no tickets"

    if result_type == "CUSTOMER_360":
        return "customer 360 snapshot"

    ticket = data.get("ticket")
    if isinstance(ticket, dict):
        return (
            f"{ticket.get('ticket_id', '')} "
            f"{ticket.get('status', '')} "
            f"{ticket.get('category', '')}"
        ).strip()

    plan = data.get("plan") or data.get("current_plan")
    if isinstance(plan, dict):
        return (
            f"{plan.get('plan_name', '')} "
            f"{plan.get('plan_id', '')} "
            f"{_money(plan.get('monthly_price'))}"
        ).strip()

    return result_type or "verified result"


def summarize_turn_facts(
    result: TruthResult[Any],
) -> str:
    if result.status == TruthStatus.VERIFIED:
        data = result.data
        if isinstance(data, dict):
            facts = _summarize_verified_data(data)
        else:
            facts = "verified"
    else:
        facts = (result.message or result.status.value).strip()

    return _truncate(facts, MAX_FACTS_CHARS)


def truncate_user_message(message: str) -> str:
    return _truncate(message, MAX_USER_MESSAGE_CHARS)
