from __future__ import annotations

import sqlite3

import pytest

from app.database.seed import seed_database
from app.handlers.cross_domain import get_customer_360
from app.llm.client import classify_deterministic_request
from app.models.domain import (
    CustomerContext,
    Intent,
    TruthStatus,
)
from app.services.chat_service import ChatService


@pytest.fixture
def db() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )
    seed_database(
        connection,
        reset=True,
    )
    return connection


def _summary(
    db: sqlite3.Connection,
    customer_id: str,
) -> dict:
    result = get_customer_360(
        db,
        CustomerContext(
            customer_id=customer_id
        ),
    )

    assert result.status == TruthStatus.VERIFIED
    return result.data


def test_customer_360_returns_all_domains_and_renderable_summary(
    db: sqlite3.Connection,
) -> None:
    class DeterministicClient:
        def extract_intent(
            self,
            user_message: str,
        ):
            return classify_deterministic_request(
                user_message
            )

    response = ChatService(
        DeterministicClient()
    ).respond(
        db=db,
        customer=CustomerContext(
            customer_id="CUST002"
        ),
        user_message="Give me a summary of my account.",
    )

    assert response.status == "VERIFIED"
    assert response.presentation is not None
    assert response.presentation.type == "customer_360"
    assert response.presentation.title == "Customer 360"
    tables = {
        table.title.split(" (", maxsplit=1)[0]: table
        for table in response.presentation.tables
    }
    assert set(tables) == {
        "Customer",
        "Subscriptions",
        "Plans",
        "Usage",
        "Bills",
        "Bill Items",
        "Payments",
        "Support Tickets",
        "Devices",
    }
    assert tables["Customer"].rows[0]["email"] == "diya.mehta@example.com"
    assert len(tables["Bills"].rows) > 1
    assert len(tables["Usage"].rows) > 1
    assert tables["Payments"].rows[0]["status"] == "FAILED"
    assert tables["Support Tickets"].rows[0]["ticket_id"] == "TKT003"
    assert "You've used 54 GB of 75 GB this cycle" in response.message
    assert "₹1,143 — Unpaid" in response.message
    assert "Your latest payment of ₹1,143 was unsuccessful." in response.message
    assert "Samsung Galaxy S24" in response.message
    assert "TKT003" not in response.message
    assert "Customer 360" not in response.message


@pytest.mark.parametrize(
    "question",
    [
        "Give me a summary of my account.",
        "Show my account overview.",
        "Give me my Customer 360.",
        "What's happening with my account?",
        "Summarize my NexaTel account.",
        "How am I doing overall?",
    ],
)
def test_customer_360_demo_questions_route_to_one_intent(
    question: str,
) -> None:
    response = classify_deterministic_request(
        question
    )

    assert response is not None
    assert response.intent == Intent.GET_CUSTOMER_360


@pytest.mark.parametrize(
    "question",
    [
        "Is anything wrong with my account?",
        "Does anything need my attention?",
        "Is anything pending on my account?",
        "What should I know about my account?",
        "Is there anything I need to take care of?",
    ],
)
def test_attention_questions_use_phase_five_rules(
    question: str,
) -> None:
    response = classify_deterministic_request(
        question
    )

    assert response is not None
    assert response.intent == Intent.GET_ACCOUNT_ATTENTION_SUMMARY


def test_customer_360_reports_unpaid_bill_failed_payment_and_urgent_ticket(
    db: sqlite3.Connection,
) -> None:
    summary = _summary(
        db,
        "CUST002",
    )

    assert summary["billing"]["amount"] == 1143
    assert summary["billing"]["status"] == "UNPAID"
    assert summary["payment"]["latest_attempt"]["status"] == "FAILED"
    assert summary["payment"]["outstanding_amount"] == 1143
    assert summary["support"]["unresolved_count"] == 1
    assert summary["support"]["important_ticket"] == {
        "ticket_id": "TKT003",
        "category": "BILLING",
        "status": "OPEN",
        "priority": "HIGH",
    }


def test_customer_360_prioritizes_critical_ticket_over_high_priority(
    db: sqlite3.Connection,
) -> None:
    db.execute(
        """
        INSERT INTO support_tickets (
            ticket_id,
            customer_id,
            category,
            description,
            status,
            priority,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "TKT-C360-CRITICAL",
            "CUST002",
            "PAYMENT",
            "Recorded critical support case",
            "IN_PROGRESS",
            "CRITICAL",
            "2026-01-01T10:00:00",
            "2026-01-02T10:00:00",
        ),
    )

    summary = _summary(
        db,
        "CUST002",
    )

    assert summary["support"]["important_ticket"]["ticket_id"] == "TKT-C360-CRITICAL"
    assert summary["support"]["important_ticket"]["priority"] == "CRITICAL"


def test_customer_360_reuses_high_usage_attention_calculation(
    db: sqlite3.Connection,
) -> None:
    summary = _summary(
        db,
        "CUST006",
    )

    assert summary["usage"]["consumed_percentage"] >= 85
    assert any(
        item["domain"] == "Usage"
        for item in summary["attention"]["items"]
    )


def test_customer_360_preserves_partial_and_pending_reconciliation(
    db: sqlite3.Connection,
) -> None:
    partial = _summary(
        db,
        "CUST006",
    )

    assert partial["billing"]["status"] == "PARTIALLY_PAID"
    assert partial["payment"]["latest_attempt"]["status"] == "SUCCESS"
    assert partial["payment"]["outstanding_amount"] == 549.45

    db.execute(
        "UPDATE payments SET status = 'PENDING' WHERE payment_id = ?",
        (partial["payment"]["latest_attempt"]["payment_id"],),
    )

    pending = _summary(
        db,
        "CUST006",
    )

    assert pending["payment"]["latest_attempt"]["status"] == "PENDING"
    assert pending["payment"]["outstanding_amount"] == 999


def test_customer_360_reports_suspended_and_cancelled_states(
    db: sqlite3.Connection,
) -> None:
    suspended = _summary(
        db,
        "CUST004",
    )
    cancelled = _summary(
        db,
        "CUST007",
    )

    assert suspended["account"]["account_status"] == "SUSPENDED"
    assert suspended["subscription"]["subscription_status"] == "SUSPENDED"
    assert cancelled["account"]["account_status"] == "CANCELLED"
    assert cancelled["subscription"]["subscription_status"] == "CANCELLED"


def test_account_plan_prefers_active_subscription_over_older_records(
    db: sqlite3.Connection,
) -> None:
    db.execute(
        """
        INSERT INTO subscriptions (
            subscription_id,
            customer_id,
            plan_id,
            activation_date,
            status,
            renewal_date
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "SUB-C360-CANCELLED",
            "CUST002",
            "PLAN001",
            "2026-01-01",
            "CANCELLED",
            "2026-02-01",
        ),
    )

    summary = _summary(
        db,
        "CUST002",
    )

    assert summary["subscription"]["subscription_status"] == "ACTIVE"
    assert summary["plan"]["plan_name"] == "NexaMax 799"


def test_customer_360_handles_unlimited_fiber_without_remaining_gb(
    db: sqlite3.Connection,
) -> None:
    summary = _summary(
        db,
        "CUST003",
    )

    assert summary["plan"]["plan_type"] == "FIBER"
    assert summary["usage"]["is_unlimited"] is True
    assert summary["usage"]["remaining"] is None


def test_customer_360_handles_healthy_account_without_warnings(
    db: sqlite3.Connection,
) -> None:
    summary = _summary(
        db,
        "CUST005",
    )

    assert summary["account"]["account_status"] == "ACTIVE"
    assert summary["attention"]["count"] == 0
    assert summary["attention"]["items"] == []


def test_customer_360_handles_multiple_active_devices(
    db: sqlite3.Connection,
) -> None:
    db.execute(
        """
        INSERT INTO devices (
            device_id,
            customer_id,
            device_name,
            device_type,
            purchase_date,
            status
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "DEV-C360-002",
            "CUST002",
            "Nexa Tablet",
            "TABLET",
            "2026-08-01",
            "ACTIVE",
        ),
    )

    summary = _summary(
        db,
        "CUST002",
    )

    assert summary["devices"]["active_count"] == 2
    assert {
        device["device_name"]
        for device in summary["devices"]["active_devices"]
    } == {
        "Samsung Galaxy S24",
        "Nexa Tablet",
    }


def test_customer_360_distinguishes_missing_optional_records(
    db: sqlite3.Connection,
) -> None:
    db.execute(
        "DELETE FROM payments WHERE customer_id = ?",
        ("CUST002",),
    )
    db.execute(
        "DELETE FROM support_tickets WHERE customer_id = ?",
        ("CUST002",),
    )
    db.execute(
        "DELETE FROM devices WHERE customer_id = ?",
        ("CUST002",),
    )
    db.execute(
        "DELETE FROM usage WHERE customer_id = ?",
        ("CUST002",),
    )

    summary = _summary(
        db,
        "CUST002",
    )

    assert summary["payment"]["attempt_count"] == 0
    assert summary["payment"]["latest_attempt"] is None
    assert summary["payment"]["outstanding_amount"] == 1143
    assert summary["support"]["unresolved_count"] == 0
    assert summary["support"]["important_ticket"] is None
    assert summary["devices"]["available"] is False
    assert summary["usage"] is None
    assert "required usage records" in summary["usage_message"]

    class DeterministicClient:
        def extract_intent(
            self,
            user_message: str,
        ):
            return classify_deterministic_request(
                user_message
            )

    response = ChatService(
        DeterministicClient()
    ).respond(
        db=db,
        customer=CustomerContext(
            customer_id="CUST002"
        ),
        user_message="Show my account overview.",
    )

    assert "No payment attempt is recorded for this bill." in response.message
    assert "No devices are currently associated with your account." in response.message
    assert "I can see your current plan" in response.message
    assert "don't have the required usage records" in response.message
    assert response.presentation is not None
    assert response.presentation.type == "customer_360"
    tables = {
        table.title.split(" (", maxsplit=1)[0]: table
        for table in response.presentation.tables
    }
    assert tables["Payments"].rows == []
    assert tables["Support Tickets"].rows == []
    assert tables["Devices"].rows == []
    assert tables["Usage"].rows == []


def test_customer_360_isolates_each_customer_data(
    db: sqlite3.Connection,
) -> None:
    other_customer = _summary(
        db,
        "CUST001",
    )
    demo_customer = _summary(
        db,
        "CUST002",
    )

    assert demo_customer["support"]["important_ticket"]["ticket_id"] == "TKT003"
    assert other_customer["support"]["important_ticket"] is None
    assert "Samsung Galaxy S24" not in str(other_customer["devices"])

    demo_records = _summary(
        db,
        "CUST002",
    )["records"]
    other_records = _summary(
        db,
        "CUST001",
    )["records"]

    assert demo_records["customer"][0]["customer_id"] == "CUST002"
    assert all(
        row["customer_id"] == "CUST002"
        for table in (
            "subscriptions",
            "usage",
            "bills",
            "payments",
            "support_tickets",
            "devices",
        )
        for row in demo_records[table]
    )
    assert other_records["customer"][0]["customer_id"] == "CUST001"
    assert all(
        row["customer_id"] == "CUST001"
        for table in (
            "subscriptions",
            "usage",
            "bills",
            "payments",
            "support_tickets",
            "devices",
        )
        for row in other_records[table]
    )