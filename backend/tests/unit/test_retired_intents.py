"""Retired intent routing."""

import sqlite3

import pytest

from app.database.seed import seed_database
from app.intent.retired import RETIRED_INTENTS
from app.intent.router import IntentRouter
from app.models.domain import CustomerContext, Intent, TruthStatus
from app.models.llm import IntentParameters, LLMIntentResponse


@pytest.mark.parametrize(
    "intent",
    sorted(RETIRED_INTENTS, key=lambda item: item.value),
)
def test_retired_intent_returns_unsupported(
    intent: Intent,
) -> None:
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    seed_database(db, reset=True)
    router = IntentRouter()
    customer = CustomerContext(customer_id="CUST002")

    result = router.route(
        db=db,
        customer=customer,
        intent_response=LLMIntentResponse(
            intent=intent,
            parameters=IntentParameters(),
        ),
    )

    assert result.status == TruthStatus.UNSUPPORTED
    assert "simplified" in (result.message or "").lower()
    db.close()
