"""Every question in DEMO_QUESTIONS.md must route to a useful backend outcome."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import sqlite3

from app.database.seed import seed_database
from app.intent.router import IntentRouter
from app.llm.client import classify_deterministic_request
from app.models.domain import (
    CustomerContext,
    Intent,
    TruthStatus,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEMO_QUESTIONS_PATH = REPO_ROOT / "DEMO_QUESTIONS.md"

SKIP_SECTIONS = {
    "unsupported",
}

CUSTOMER_FOR_QUESTION: dict[str, str] = {
    "show bill bill009": "CUST005",
    "compare bill009 and bill010": "CUST005",
    "latest update on ticket tkt003": "CUST002",
    "show the full timeline for ticket tkt003": "CUST002",
    "did my last payment fail": "CUST002",
    "list my failed payments": "CUST002",
    "show my mobile bill": "CUST003",
    "show my fiber bill": "CUST003",
    "do i have a router": "CUST003",
    "is my account active, suspended, or cancelled": "CUST004",
    "payment with reference txn2026000006": "CUST005",
    "show device dev001": "CUST003",
}


def _load_demo_questions() -> list[tuple[str, str]]:
    text = DEMO_QUESTIONS_PATH.read_text(encoding="utf-8")
    section = "general"
    items: list[tuple[str, str]] = []

    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
            continue
        match = re.match(r"^-\s+(.+)$", line.strip())
        if not match:
            continue
        question = match.group(1).strip()
        items.append((section, question))

    return items


def _customer_for(question: str) -> str:
    key = question.lower().strip().rstrip(".")
    for fragment, customer_id in CUSTOMER_FOR_QUESTION.items():
        if fragment in key:
            return customer_id
    return "CUST005"


@pytest.fixture
def db() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    seed_database(connection, reset=True)
    yield connection
    connection.close()


@pytest.mark.parametrize(
    ("section", "question"),
    _load_demo_questions(),
    ids=lambda value: (
        value if isinstance(value, str) and len(value) < 60 else "row"
    ),
)
def test_demo_question_is_answerable(
    section: str,
    question: str,
    db: sqlite3.Connection,
) -> None:
    if any(skip in section for skip in SKIP_SECTIONS):
        intent_response = classify_deterministic_request(question)
        assert intent_response is not None
        assert intent_response.intent == Intent.UNSUPPORTED
        assert intent_response.clarification
        return

    intent_response = classify_deterministic_request(question)
    assert intent_response is not None, (
        f"No deterministic intent for: {question}"
    )

    if section == "clarifications":
        assert intent_response.intent == Intent.UNSUPPORTED
        assert intent_response.clarification
        return

    assert intent_response.intent != Intent.UNSUPPORTED, question

    customer_id = _customer_for(question)
    router = IntentRouter()
    result = router.route(
        db=db,
        customer=CustomerContext(customer_id=customer_id),
        intent_response=intent_response,
    )

    assert result.status in {
        TruthStatus.VERIFIED,
        TruthStatus.NOT_FOUND,
        TruthStatus.AMBIGUOUS,
    }, (
        f"{question} -> {intent_response.intent.value}: "
        f"{result.status} {result.message}"
    )
