from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.api.routes.chat import conversation_service as api_conversation_service
from app.database.seed import seed_database
from app.llm.client import classify_deterministic_request
from app.models.domain import (
    CustomerContext,
    Intent,
    SupportTicketStatus,
    TimeRange,
    UsageType,
)
from app.models.llm import (
    IntentParameters,
    LLMIntentResponse,
)
from app.services.chat_service import ChatService
from app.services.conversation_service import (
    ConversationContext,
    ConversationService,
)
from app.main import app


class ScriptedIntentClient:
    """Use explicit requests as fixtures; follow-ups use context resolution."""

    def extract_intent(
        self,
        user_message: str,
        *,
        context_hint: str | None = None,
    ) -> LLMIntentResponse:
        text = user_message.lower().strip()

        if "current bill" in text or text == "what's my bill?":
            return LLMIntentResponse(
                intent=Intent.GET_CURRENT_BILL
            )

        if "compare august and september bills" in text:
            return LLMIntentResponse(
                intent=Intent.GET_BILL_COMPARISON,
                parameters=IntentParameters(
                    month=9,
                    year=2026,
                    comparison_month=8,
                    comparison_year=2026,
                ),
            )

        if "how much data have i used" in text:
            return LLMIntentResponse(
                intent=Intent.GET_DATA_USAGE,
                parameters=IntentParameters(
                    time_range=TimeRange.CURRENT_MONTH,
                ),
            )

        if "open tickets" in text:
            return LLMIntentResponse(
                intent=Intent.GET_SUPPORT_TICKETS,
                parameters=IntentParameters(
                    ticket_status=SupportTicketStatus.OPEN
                ),
            )

        if "show my devices" in text:
            return LLMIntentResponse(
                intent=Intent.GET_DEVICE_INFORMATION
            )

        if "what's my plan" in text:
            return LLMIntentResponse(
                intent=Intent.GET_CURRENT_PLAN
            )

        deterministic = classify_deterministic_request(
            user_message
        )
        if deterministic is not None:
            return deterministic

        return LLMIntentResponse(
            intent=Intent.UNSUPPORTED
        )


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


@pytest.fixture
def conversation_service() -> ConversationService:
    return ConversationService()


@pytest.fixture
def chat(
    conversation_service: ConversationService,
) -> ChatService:
    return ChatService(
        ScriptedIntentClient(),
        conversation_service=conversation_service,
    )


def _ask(
    chat: ChatService,
    db: sqlite3.Connection,
    message: str,
    *,
    customer_id: str = "CUST002",
    conversation_id: str = "conversation-1",
):
    return chat.respond(
        db=db,
        customer=CustomerContext(
            customer_id=customer_id
        ),
        user_message=message,
        conversation_id=conversation_id,
    )


def test_bill_explanation_breakdown_and_payment_followups(
    chat: ChatService,
    db: sqlite3.Connection,
) -> None:
    bill = _ask(
        chat,
        db,
        "What's my current bill?",
    )
    explanation = _ask(
        chat,
        db,
        "Why is it higher?",
    )
    breakdown = _ask(
        chat,
        db,
        "What extra charges are there?",
    )
    payment = _ask(
        chat,
        db,
        "Did I try paying it?",
    )
    payment_status = _ask(
        chat,
        db,
        "Did that payment succeed?",
    )

    assert bill.status == "VERIFIED"
    assert "₹1,143" in bill.message
    assert explanation.status == "VERIFIED"
    assert breakdown.status == "VERIFIED"
    assert payment.status == "VERIFIED"
    assert "latest recorded payment attempt is failed" in payment.message
    assert payment_status.status == "VERIFIED"
    assert "recorded as failed" in payment_status.message


def test_bill_payment_followup_preserves_subject_for_support(
    chat: ChatService,
    conversation_service: ConversationService,
    db: sqlite3.Connection,
) -> None:
    _ask(
        chat,
        db,
        "What's my current bill?",
    )
    payment = _ask(
        chat,
        db,
        "Did I try paying it?",
    )
    support = _ask(
        chat,
        db,
        "Do I already have a complaint about this?",
    )
    update = _ask(
        chat,
        db,
        "When was it last updated?",
    )

    assert payment.status == "VERIFIED"
    assert support.status == "VERIFIED"
    assert "billing-category" in support.message
    assert "not establish that they are linked" in support.message
    assert update.status == "VERIFIED"
    assert "TKT003" in update.message
    assert conversation_service.get_context(
        "conversation-1",
        CustomerContext(customer_id="CUST002"),
    ).referenced_ticket_id == "TKT003"


def test_usage_remaining_last_month_and_explicit_comparison(
    chat: ChatService,
    db: sqlite3.Connection,
) -> None:
    current = _ask(
        chat,
        db,
        "How much data have I used?",
    )
    remaining = _ask(
        chat,
        db,
        "How much is left?",
    )
    previous = _ask(
        chat,
        db,
        "What about last month?",
    )
    this_month = _ask(
        chat,
        db,
        "What about this month?",
    )
    comparison = _ask(
        chat,
        db,
        "Was that more than August?",
    )

    assert current.status == "VERIFIED"
    assert remaining.status == "VERIFIED"
    assert previous.status == "VERIFIED"
    assert this_month.status == "VERIFIED"
    assert comparison.status == "VERIFIED"
    assert "August" in previous.message
    assert "September" in this_month.message
    assert "September" in comparison.message
    assert "August" in comparison.message


def test_open_ticket_priority_and_update_followups(
    chat: ChatService,
    db: sqlite3.Connection,
) -> None:
    tickets = _ask(
        chat,
        db,
        "Do I have open tickets?",
    )
    priority = _ask(
        chat,
        db,
        "Which one is high priority?",
    )
    updated = _ask(
        chat,
        db,
        "When was it last updated?",
    )

    assert tickets.status == "VERIFIED"
    assert priority.status == "VERIFIED"
    assert priority.presentation is not None
    assert priority.presentation.type == "table"
    assert priority.presentation.rows[0]["ticket"] == "TKT003"
    assert updated.status == "VERIFIED"
    assert "TKT003" in updated.message
    assert "last updated on" in updated.message


def test_device_list_active_and_newest_followups(
    chat: ChatService,
    db: sqlite3.Connection,
) -> None:
    devices = _ask(
        chat,
        db,
        "Show my devices.",
        customer_id="CUST002",
        conversation_id="devices",
    )
    active = _ask(
        chat,
        db,
        "Which ones are active?",
        customer_id="CUST002",
        conversation_id="devices",
    )
    newest = _ask(
        chat,
        db,
        "Which is the newest?",
        customer_id="CUST002",
        conversation_id="devices",
    )

    assert devices.status == "VERIFIED"
    assert active.status == "VERIFIED"
    assert active.presentation is not None
    assert active.presentation.type == "list"
    assert active.presentation.items[0].label == "Samsung Galaxy S24"
    assert newest.status == "VERIFIED"
    assert "Samsung Galaxy A55 5G" in newest.message


def test_customer_360_followup_resolves_attention(
    chat: ChatService,
    db: sqlite3.Connection,
) -> None:
    overview = _ask(
        chat,
        db,
        "Give me a summary of my account.",
    )
    attention = _ask(
        chat,
        db,
        "What needs my attention?",
    )

    assert overview.status == "VERIFIED"
    assert overview.presentation is not None
    assert overview.presentation.type == "customer_360"
    assert attention.status == "VERIFIED"
    assert "unpaid" in attention.message
    assert "failed" in attention.message


def test_topic_switch_changes_followup_domain(
    chat: ChatService,
    db: sqlite3.Connection,
) -> None:
    _ask(
        chat,
        db,
        "What's my current bill?",
        conversation_id="topic-switch",
    )
    usage = _ask(
        chat,
        db,
        "How much data have I used?",
        conversation_id="topic-switch",
    )
    previous = _ask(
        chat,
        db,
        "What about last month?",
        conversation_id="topic-switch",
    )

    assert usage.status == "VERIFIED"
    assert previous.status == "VERIFIED"
    assert "August" in previous.message


def test_explicit_period_overrides_previous_period(
    chat: ChatService,
    db: sqlite3.Connection,
) -> None:
    _ask(
        chat,
        db,
        "How much data have I used?",
        conversation_id="explicit-period",
    )
    comparison = _ask(
        chat,
        db,
        "Compare August and September bills.",
        conversation_id="explicit-period",
    )
    july = _ask(
        chat,
        db,
        "What about July?",
        conversation_id="explicit-period",
    )

    assert comparison.status == "VERIFIED"
    assert july.status == "VERIFIED"
    assert "July" in july.message


def test_previous_one_refers_to_prior_compared_bill(
    chat: ChatService,
    db: sqlite3.Connection,
) -> None:
    comparison = _ask(
        chat,
        db,
        "Compare August and September bills.",
        conversation_id="previous-bill",
    )
    previous = _ask(
        chat,
        db,
        "What about the previous one?",
        conversation_id="previous-bill",
    )

    assert comparison.status == "VERIFIED"
    assert previous.status == "VERIFIED"
    assert "August 2026" in previous.message


def test_ambiguous_status_without_context_clarifies(
    chat: ChatService,
    db: sqlite3.Connection,
) -> None:
    response = _ask(
        chat,
        db,
        "What's the status?",
        conversation_id="ambiguous-status",
    )

    assert response.status == "AMBIGUOUS"
    assert "bill, payment, subscription, or support ticket" in response.message
    assert len(response.options) == 4


def test_new_conversation_reset_clears_references(
    conversation_service: ConversationService,
) -> None:
    customer = CustomerContext(
        customer_id="CUST002"
    )
    context = conversation_service.get_context(
        "reset-me",
        customer,
    )
    context.active_domain = "billing"
    context.referenced_bill_id = "BILL014"

    conversation_service.clear(
        "reset-me",
        customer,
    )
    reset_context = conversation_service.get_context(
        "reset-me",
        customer,
    )

    assert reset_context is not context
    assert reset_context.referenced_bill_id is None
    assert reset_context.active_domain is None


def test_customer_switch_resets_context_for_same_id(
    conversation_service: ConversationService,
) -> None:
    old_context = conversation_service.get_context(
        "switch-customer",
        CustomerContext(customer_id="CUST002"),
    )
    old_context.referenced_bill_id = "BILL014"
    old_context.active_domain = "billing"

    new_context = conversation_service.get_context(
        "switch-customer",
        CustomerContext(customer_id="CUST001"),
    )

    assert new_context is not old_context
    assert new_context.customer_id == "CUST001"
    assert new_context.referenced_bill_id is None


def test_customer_context_does_not_leak_through_chat_service(
    chat: ChatService,
    conversation_service: ConversationService,
    db: sqlite3.Connection,
) -> None:
    _ask(
        chat,
        db,
        "What's my current bill?",
        customer_id="CUST002",
        conversation_id="customer-bound",
    )
    before = conversation_service.get_context(
        "customer-bound",
        CustomerContext(customer_id="CUST002"),
    )
    assert before.referenced_bill_id == "BILL014"

    new_customer_context = conversation_service.get_context(
        "customer-bound",
        CustomerContext(customer_id="CUST001"),
    )
    response = _ask(
        chat,
        db,
        "Why is it higher?",
        customer_id="CUST001",
        conversation_id="customer-bound",
    )

    assert new_customer_context.referenced_bill_id is None
    assert response.status == "UNSUPPORTED"
    assert "BILL014" not in response.message


def test_ambiguous_followup_does_not_mutate_context(
    conversation_service: ConversationService,
) -> None:
    context = ConversationContext(
        customer_id="CUST001",
        active_domain=None,
    )

    response = conversation_service.resolve_followup(
        "What's the status?",
        context,
    )

    assert response is not None
    assert response.clarification is not None
    assert context.last_intent is None
    assert context.active_domain is None


def test_manager_demo_conversation_uses_canonical_seed_data(
    chat: ChatService,
    db: sqlite3.Connection,
) -> None:
    questions = (
        "What's my current bill?",
        "Why is it higher?",
        "What extra charges are there?",
        "Did I try paying it?",
        "Did that payment succeed?",
        "Do I already have a complaint about this?",
        "What's my plan?",
        "How much data have I used?",
        "How much is left?",
        "Give me a summary of my account.",
        "Is there anything I need to take care of?",
    )

    responses = [
        _ask(
            chat,
            db,
            question,
            conversation_id="manager-demo",
        )
        for question in questions
    ]

    assert all(
        response.status == "VERIFIED"
        for response in responses
    )
    assert "₹1,143" in responses[0].message
    assert responses[2].presentation is not None
    assert "Roaming" in str(
        responses[2].presentation.model_dump()
    )
    assert "recorded as failed" in responses[4].message
    assert "billing-category" in responses[5].message
    assert "NexaMax 799" in responses[6].message
    assert "54 GB" in responses[7].message
    assert "21 GB" in responses[8].message
    assert "Samsung Galaxy S24" in responses[9].message
    assert "failed" in responses[10].message


def test_reset_endpoint_clears_customer_conversation_context() -> None:
    customer = CustomerContext(
        customer_id="CUST002"
    )
    context = api_conversation_service.get_context(
        "api-reset-test",
        customer,
    )
    context.active_domain = "billing"
    context.referenced_bill_id = "BILL014"

    response = TestClient(app).post(
        "/api/chat/reset",
        headers={
            "X-Customer-ID": "CUST002"
        },
        json={
            "conversation_id": "api-reset-test"
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "cleared"
    }

    reset_context = api_conversation_service.get_context(
        "api-reset-test",
        customer,
    )
    assert reset_context.referenced_bill_id is None
    assert reset_context.active_domain is None