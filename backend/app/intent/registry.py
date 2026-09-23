"""Registry of supported NexaTel intents."""

from __future__ import annotations

from app.intent.definitions import (
    INTENT_DEFINITIONS,
    IntentDefinition,
)
from app.models.domain import Intent


INTENT_REGISTRY: dict[Intent, IntentDefinition] = {
    definition.intent: definition
    for definition in INTENT_DEFINITIONS
}


def get_intent_definition(
    intent: Intent,
) -> IntentDefinition:
    """Return the definition for a supported intent."""

    try:
        return INTENT_REGISTRY[intent]
    except KeyError as exc:
        raise ValueError(
            f"Intent is not registered: {intent}"
        ) from exc