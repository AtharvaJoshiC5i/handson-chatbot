"""Smart bill anomaly, plan recommendation, and proactive alerts."""

from __future__ import annotations

import sqlite3

from app.database.seed import seed_database
from app.handlers.cross_domain import get_account_attention_summary
from app.handlers.smart_features import (
    detect_bill_anomaly,
    recommend_plan_for_customer,
)
from app.llm.client import classify_deterministic_request
from app.models.domain import (
    CustomerContext,
    Intent,
    TruthStatus,
)


def _db() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    seed_database(connection, reset=True)
    return connection


def test_bill_anomaly_for_cust002_includes_roaming_driver() -> None:
    db = _db()
    result = detect_bill_anomaly(
        db,
        CustomerContext(customer_id="CUST002"),
    )
    assert result.status == TruthStatus.VERIFIED
    data = result.data or {}
    assert data["result_type"] == "BILL_ANOMALY_DETECTION"
    assert float(data["total_difference"]) == 341.0
    assert data.get("comparison_scope") == (
        "September 2026 vs August 2026"
    )
    breakdown = data.get("breakdown_lines") or []
    explained = round(
        sum(float(line["amount"]) for line in breakdown),
        2,
    )
    assert explained == float(data["total_difference"])
    labels = " ".join(
        str(line.get("label", "")).lower()
        for line in breakdown
    )
    assert "roaming" in labels
    assert "plan" in labels
    drivers = data.get("main_drivers") or []
    assert drivers and float(drivers[0]["amount"]) == 344.0
    db.close()


def test_plan_recommendation_classifies_and_returns_verified() -> None:
    classified = classify_deterministic_request(
        "Am I on the right plan?",
    )
    assert classified is not None
    assert classified.intent == Intent.GET_PLAN_RECOMMENDATION

    db = _db()
    result = recommend_plan_for_customer(
        db,
        CustomerContext(customer_id="CUST005"),
    )
    assert result.status == TruthStatus.VERIFIED
    assert result.data is not None
    assert result.data["result_type"] == "PLAN_RECOMMENDATION"
    assert result.data.get("recommendation_reasons")
    db.close()


def test_plan_recommendation_switch_includes_usage_and_savings_reasons() -> (
    None
):
    db = _db()
    result = recommend_plan_for_customer(
        db,
        CustomerContext(customer_id="CUST001"),
    )
    data = result.data or {}
    assert data["recommendation_status"] == "SWITCH_RECOMMENDED"
    reasons = " ".join(data.get("recommendation_reasons") or []).lower()
    assert "gb" in reasons
    assert "nexamax 499" in reasons
    assert float(data["estimated_monthly_savings"]) > 0
    db.close()


def test_attention_summary_includes_proactive_messages() -> None:
    db = _db()
    result = get_account_attention_summary(
        db,
        CustomerContext(customer_id="CUST002"),
    )
    assert result.status == TruthStatus.VERIFIED
    items = (result.data or {}).get("items") or []
    messages = " ".join(
        item["message"] for item in items
    ).lower()
    assert (
        "payment" in messages
        or "bill" in messages
        or "renew" in messages
    )
    db.close()
