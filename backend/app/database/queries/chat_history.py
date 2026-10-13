"""Persisted chat conversations and messages."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from uuid import uuid4


_CHAT_HISTORY_DDL = """
CREATE TABLE IF NOT EXISTS chat_conversations (
    conversation_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL
        CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    status TEXT,
    source TEXT,
    presentation_json TEXT,
    options_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (conversation_id)
        REFERENCES chat_conversations(conversation_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chat_conversations_customer_updated
    ON chat_conversations(customer_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation_created
    ON chat_messages(conversation_id, created_at ASC);
"""


def ensure_chat_history_schema(
    db: sqlite3.Connection,
) -> None:
    db.executescript(_CHAT_HISTORY_DDL)
    try:
        db.execute(
            "ALTER TABLE chat_messages "
            "ADD COLUMN presentation_meta_json TEXT"
        )
        db.commit()
    except sqlite3.OperationalError:
        pass


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _title_from_message(message: str) -> str:
    collapsed = " ".join(message.split())
    if len(collapsed) <= 72:
        return collapsed
    return f"{collapsed[:69].rstrip()}…"


def upsert_conversation(
    db: sqlite3.Connection,
    *,
    conversation_id: str,
    customer_id: str,
    title: str | None = None,
) -> None:
    ensure_chat_history_schema(db)
    now = _utc_now_iso()
    cursor = db.execute(
        """
        SELECT conversation_id
        FROM chat_conversations
        WHERE conversation_id = ?
        """,
        (conversation_id,),
    )
    existing = cursor.fetchone()

    if existing is None:
        resolved_title = title or "New conversation"
        db.execute(
            """
            INSERT INTO chat_conversations (
                conversation_id,
                customer_id,
                title,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                customer_id,
                resolved_title,
                now,
                now,
            ),
        )
        return

    if title:
        db.execute(
            """
            UPDATE chat_conversations
            SET title = ?, updated_at = ?
            WHERE conversation_id = ?
              AND customer_id = ?
            """,
            (title, now, conversation_id, customer_id),
        )
    else:
        db.execute(
            """
            UPDATE chat_conversations
            SET updated_at = ?
            WHERE conversation_id = ?
              AND customer_id = ?
            """,
            (now, conversation_id, customer_id),
        )


def insert_message(
    db: sqlite3.Connection,
    *,
    conversation_id: str,
    customer_id: str,
    role: str,
    content: str,
    status: str | None = None,
    source: str | None = None,
    presentation: dict[str, object] | None = None,
    presentation_meta: dict[str, object] | None = None,
    options: list[dict[str, str]] | None = None,
    user_message_for_title: str | None = None,
) -> str:
    ensure_chat_history_schema(db)
    message_id = uuid4().hex
    now = _utc_now_iso()

    if role == "user" and user_message_for_title:
        upsert_conversation(
            db,
            conversation_id=conversation_id,
            customer_id=customer_id,
            title=_title_from_message(user_message_for_title),
        )
    else:
        upsert_conversation(
            db,
            conversation_id=conversation_id,
            customer_id=customer_id,
        )

    db.execute(
        """
        INSERT INTO chat_messages (
            message_id,
            conversation_id,
            role,
            content,
            status,
            source,
            presentation_json,
            presentation_meta_json,
            options_json,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            message_id,
            conversation_id,
            role,
            content,
            status,
            source,
            json.dumps(presentation, ensure_ascii=False)
            if presentation is not None
            else None,
            json.dumps(presentation_meta, ensure_ascii=False)
            if presentation_meta is not None
            else None,
            json.dumps(options, ensure_ascii=False)
            if options is not None
            else None,
            now,
        ),
    )
    db.commit()
    return message_id


def list_conversations(
    db: sqlite3.Connection,
    *,
    customer_id: str | None = None,
    limit: int = 40,
) -> list[sqlite3.Row]:
    ensure_chat_history_schema(db)
    capped = max(1, min(limit, 100))

    if customer_id:
        cursor = db.execute(
            """
            SELECT
                c.conversation_id,
                c.customer_id,
                cust.name AS customer_name,
                c.title,
                c.created_at,
                c.updated_at
            FROM chat_conversations AS c
            INNER JOIN customers AS cust
                ON cust.customer_id = c.customer_id
            WHERE c.customer_id = ?
            ORDER BY c.updated_at DESC
            LIMIT ?
            """,
            (customer_id, capped),
        )
    else:
        cursor = db.execute(
            """
            SELECT
                c.conversation_id,
                c.customer_id,
                cust.name AS customer_name,
                c.title,
                c.created_at,
                c.updated_at
            FROM chat_conversations AS c
            INNER JOIN customers AS cust
                ON cust.customer_id = c.customer_id
            ORDER BY c.updated_at DESC
            LIMIT ?
            """,
            (capped,),
        )

    return list(cursor.fetchall())


def get_conversation_messages(
    db: sqlite3.Connection,
    *,
    conversation_id: str,
    customer_id: str,
) -> list[sqlite3.Row]:
    ensure_chat_history_schema(db)
    cursor = db.execute(
        """
        SELECT
            m.message_id,
            m.conversation_id,
            m.role,
            m.content,
            m.status,
            m.source,
            m.presentation_json,
            m.presentation_meta_json,
            m.options_json,
            m.created_at
        FROM chat_messages AS m
        INNER JOIN chat_conversations AS c
            ON c.conversation_id = m.conversation_id
        WHERE m.conversation_id = ?
          AND c.customer_id = ?
        ORDER BY
            m.created_at ASC,
            CASE m.role
                WHEN 'user' THEN 0
                ELSE 1
            END,
            m.message_id ASC
        """,
        (conversation_id, customer_id),
    )
    return list(cursor.fetchall())


def delete_conversation(
    db: sqlite3.Connection,
    *,
    conversation_id: str,
    customer_id: str,
) -> bool:
    ensure_chat_history_schema(db)
    cursor = db.execute(
        """
        DELETE FROM chat_conversations
        WHERE conversation_id = ?
          AND customer_id = ?
        """,
        (conversation_id, customer_id),
    )
    db.commit()
    return cursor.rowcount > 0
