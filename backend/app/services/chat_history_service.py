"""Record and load persisted chat history."""

from __future__ import annotations

import json
import sqlite3

from app.database.queries.chat_history import (
    get_conversation_messages,
    insert_message,
    list_conversations,
)
from app.models.api import (
    ChatOption,
    ChatPresentation,
    PresentationMeta,
)


class ChatHistoryService:
    def record_exchange(
        self,
        db: sqlite3.Connection,
        *,
        conversation_id: str,
        customer_id: str,
        user_message: str,
        assistant_message: str,
        status: str,
        source: str | None,
        presentation: ChatPresentation | None,
        presentation_meta: PresentationMeta | None = None,
        options: list[ChatOption] | None = None,
    ) -> None:
        presentation_payload = (
            presentation.model_dump(mode="json")
            if presentation is not None
            else None
        )
        meta_payload = (
            presentation_meta.model_dump(mode="json")
            if presentation_meta is not None
            else None
        )
        resolved_options = options or []
        options_payload = [
            {"label": option.label, "message": option.message}
            for option in resolved_options
        ]

        insert_message(
            db,
            conversation_id=conversation_id,
            customer_id=customer_id,
            role="user",
            content=user_message,
            user_message_for_title=user_message,
        )
        insert_message(
            db,
            conversation_id=conversation_id,
            customer_id=customer_id,
            role="assistant",
            content=assistant_message,
            status=status,
            source=source,
            presentation=presentation_payload,
            presentation_meta=meta_payload,
            options=options_payload,
        )

    def list_for_customer(
        self,
        db: sqlite3.Connection,
        customer_id: str,
        *,
        limit: int = 40,
    ) -> list[sqlite3.Row]:
        return list_conversations(
            db,
            customer_id=customer_id,
            limit=limit,
        )

    def list_all(
        self,
        db: sqlite3.Connection,
        *,
        limit: int = 40,
    ) -> list[sqlite3.Row]:
        return list_conversations(db, customer_id=None, limit=limit)

    def load_messages(
        self,
        db: sqlite3.Connection,
        *,
        conversation_id: str,
        customer_id: str,
    ) -> list[dict[str, object]]:
        rows = get_conversation_messages(
            db,
            conversation_id=conversation_id,
            customer_id=customer_id,
        )
        messages: list[dict[str, object]] = []

        for row in rows:
            presentation = None
            if row["presentation_json"]:
                try:
                    presentation = json.loads(row["presentation_json"])
                except json.JSONDecodeError:
                    presentation = None

            presentation_meta = None
            meta_raw = row["presentation_meta_json"]
            if meta_raw:
                try:
                    presentation_meta = json.loads(meta_raw)
                except json.JSONDecodeError:
                    presentation_meta = None

            options: list[dict[str, str]] = []
            if row["options_json"]:
                try:
                    parsed = json.loads(row["options_json"])
                    if isinstance(parsed, list):
                        options = [
                            item
                            for item in parsed
                            if isinstance(item, dict)
                        ]
                except json.JSONDecodeError:
                    options = []

            messages.append(
                {
                    "id": row["message_id"],
                    "role": row["role"],
                    "content": row["content"],
                    "status": row["status"],
                    "source": row["source"],
                    "presentation": presentation,
                    "presentation_meta": presentation_meta,
                    "options": options,
                    "created_at": row["created_at"],
                }
            )

        return messages
