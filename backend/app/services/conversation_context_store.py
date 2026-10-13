"""Persist and restore in-memory ConversationContext for resumed threads."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

from app.database.queries.chat_history import (
    ensure_chat_history_schema,
    upsert_conversation,
)
from app.services.conversation_service import ConversationContext
from app.services.conversation_turn import ConversationTurn


_CONTEXT_DDL = """
CREATE TABLE IF NOT EXISTS chat_conversation_context (
    conversation_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    context_json TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (conversation_id)
        REFERENCES chat_conversations(conversation_id)
        ON DELETE CASCADE
);
"""


def ensure_context_schema(db: sqlite3.Connection) -> None:
    ensure_chat_history_schema(db)
    db.executescript(_CONTEXT_DDL)


def _turn_to_dict(turn: ConversationTurn) -> dict[str, Any]:
    return {
        "user_message": turn.user_message,
        "intent": turn.intent,
        "status": turn.status,
        "result_type": turn.result_type,
        "domain": turn.domain,
        "facts": turn.facts,
    }


def _turn_from_dict(payload: dict[str, Any]) -> ConversationTurn:
    return ConversationTurn(
        user_message=str(payload.get("user_message", "")),
        intent=str(payload.get("intent", "")),
        status=str(payload.get("status", "")),
        result_type=payload.get("result_type"),
        domain=payload.get("domain"),
        facts=str(payload.get("facts", "")),
    )


def snapshot_context(context: ConversationContext) -> dict[str, Any]:
    return {
        "customer_id": context.customer_id,
        "last_intent": context.last_intent,
        "active_domain": context.active_domain,
        "referenced_bill_id": context.referenced_bill_id,
        "referenced_payment_id": context.referenced_payment_id,
        "referenced_payment_reference": (
            context.referenced_payment_reference
        ),
        "referenced_ticket_id": context.referenced_ticket_id,
        "referenced_device_id": context.referenced_device_id,
        "referenced_subscription_id": context.referenced_subscription_id,
        "referenced_period": context.referenced_period,
        "comparison_period": context.comparison_period,
        "usage_type": context.usage_type,
        "support_unresolved_only": context.support_unresolved_only,
        "support_ticket_status": context.support_ticket_status,
        "turns": [_turn_to_dict(turn) for turn in context.turns],
    }


def apply_snapshot(
    context: ConversationContext,
    payload: dict[str, Any],
) -> None:
    for field in (
        "last_intent",
        "active_domain",
        "referenced_bill_id",
        "referenced_payment_id",
        "referenced_payment_reference",
        "referenced_ticket_id",
        "referenced_device_id",
        "referenced_subscription_id",
        "referenced_period",
        "comparison_period",
        "usage_type",
        "support_ticket_status",
    ):
        if field in payload:
            setattr(context, field, payload.get(field))

    if "support_unresolved_only" in payload:
        context.support_unresolved_only = bool(
            payload.get("support_unresolved_only")
        )

    context.turns.clear()
    for item in payload.get("turns", []):
        if isinstance(item, dict):
            context.turns.append(_turn_from_dict(item))


def save_conversation_context(
    db: sqlite3.Connection,
    *,
    conversation_id: str,
    customer_id: str,
    context: ConversationContext,
) -> None:
    ensure_context_schema(db)
    upsert_conversation(
        db,
        conversation_id=conversation_id,
        customer_id=customer_id,
    )
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    payload = json.dumps(
        snapshot_context(context),
        ensure_ascii=False,
    )
    db.execute(
        """
        INSERT INTO chat_conversation_context (
            conversation_id,
            customer_id,
            context_json,
            updated_at
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT(conversation_id) DO UPDATE SET
            customer_id = excluded.customer_id,
            context_json = excluded.context_json,
            updated_at = excluded.updated_at
        """,
        (
            conversation_id,
            customer_id,
            payload,
            now,
        ),
    )
    db.commit()


def load_conversation_context(
    db: sqlite3.Connection,
    *,
    conversation_id: str,
    customer_id: str,
) -> dict[str, Any] | None:
    ensure_context_schema(db)
    row = db.execute(
        """
        SELECT context_json
        FROM chat_conversation_context
        WHERE conversation_id = ?
          AND customer_id = ?
        """,
        (conversation_id, customer_id),
    ).fetchone()

    if row is None:
        return None

    try:
        parsed = json.loads(row["context_json"])
    except json.JSONDecodeError:
        return None

    return parsed if isinstance(parsed, dict) else None
