"""Intents intentionally disabled in chat (none for full demo question bank)."""

from __future__ import annotations

from app.models.domain import Intent

RETIRED_INTENTS: frozenset[Intent] = frozenset()

RETIRED_INTENT_MESSAGE = (
    "That capability isn't available in this NexaTel chat demo."
)


def is_retired_intent(intent: Intent) -> bool:
    return intent in RETIRED_INTENTS


def retired_intent_message() -> str:
    return RETIRED_INTENT_MESSAGE
