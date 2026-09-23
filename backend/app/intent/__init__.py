"""Intent recognition and deterministic routing for NexaTel."""

from app.intent.definitions import IntentDefinition
from app.intent.registry import INTENT_REGISTRY, get_intent_definition
from app.intent.router import IntentRouter

__all__ = [
    "IntentDefinition",
    "INTENT_REGISTRY",
    "get_intent_definition",
    "IntentRouter",
]