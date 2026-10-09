from __future__ import annotations

from collections import deque

import pytest

from app.config.settings import get_settings
from app.models.domain import Intent, TruthStatus
from app.truth.sources import DATABASE_SOURCE
from app.models.llm import LLMIntentResponse
from app.services.conversation_service import ConversationContext
from app.services.conversation_turn import ConversationTurn
from app.services.conversation_turn_summary import (
    summarize_turn_facts,
    truncate_user_message,
)
from app.truth.result import TruthResult, verified_result


def test_turn_deque_respects_conversation_turn_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "CONVERSATION_TURN_WINDOW",
        "3",
    )
    get_settings.cache_clear()
    context = ConversationContext(customer_id="CUST001")
    intent = LLMIntentResponse(intent=Intent.GET_CURRENT_BILL)
    for index in range(5):
        context.record_turn(
            f"message {index}",
            intent,
            TruthResult(
                status=TruthStatus.NOT_FOUND,
                message="missing",
            ),
        )

    assert len(context.turns) == 3
    assert context.turns[0].user_message == "message 2"
    assert context.turns[-1].user_message == "message 4"


def test_build_intent_context_includes_snapshot_and_turns() -> None:
    context = ConversationContext(customer_id="CUST001")
    context.last_intent = Intent.GET_CURRENT_BILL.value
    context.active_domain = "billing"
    context.turns.append(
        ConversationTurn(
            user_message="What's my bill?",
            intent=Intent.GET_CURRENT_BILL.value,
            status=TruthStatus.VERIFIED.value,
            result_type="BILL_CURRENT",
            domain="billing",
            facts="2026-09 ₹797 PAID",
        )
    )

    built = context.build_intent_context()

    assert "Snapshot:" in built
    assert "last_intent=GET_CURRENT_BILL" in built
    assert "Recent turns" in built
    assert 'user="What\'s my bill?"' in built
    assert "GET_CURRENT_BILL VERIFIED" in built


def test_summarize_turn_facts_for_verified_bill() -> None:
    result = verified_result(
        {
            "result_type": "BILL_CURRENT",
            "bill": {
                "period": "2026-09",
                "amount": 797,
                "status": "PAID",
                "bill_id": "BILL009",
            },
        },
        source=DATABASE_SOURCE,
    )

    facts = summarize_turn_facts(result)

    assert "2026-09" in facts
    assert "797" in facts
    assert "PAID" in facts
    assert "BILL009" in facts


def test_truncate_user_message() -> None:
    long_text = "x" * 500
    assert len(truncate_user_message(long_text)) == 400


def test_referenced_entities_from_history() -> None:
    context = ConversationContext(customer_id="CUST001")
    context.turns = deque(
        [
            ConversationTurn(
                user_message="bill",
                intent=Intent.GET_CURRENT_BILL.value,
                status=TruthStatus.VERIFIED.value,
                result_type="BILL_CURRENT",
                domain="billing",
                facts="2026-08 ₹500 PAID BILL010",
            ),
            ConversationTurn(
                user_message="ticket",
                intent=Intent.GET_SUPPORT_TICKETS.value,
                status=TruthStatus.VERIFIED.value,
                result_type="SUPPORT_FILTER",
                domain="support",
                facts="2 tickets; TKT003 OPEN",
            ),
        ]
    )

    assert context.referenced_bill_id_from_history() == "BILL010"
    assert context.referenced_period_from_history() == "2026-08"
    assert context.referenced_ticket_id_from_history() == "TKT003"
