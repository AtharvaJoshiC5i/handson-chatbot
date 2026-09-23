"""Intent extraction service."""

from __future__ import annotations

from app.llm.client import GroqLLMClient
from app.models.llm import LLMIntentResponse


class IntentExtractor:
    """Application-facing intent extraction service."""

    def __init__(
        self,
        llm_client: GroqLLMClient,
    ) -> None:
        self._llm_client = llm_client

    def extract(
        self,
        user_message: str,
    ) -> LLMIntentResponse:
        """Extract and validate a structured intent."""

        return self._llm_client.extract_intent(
            user_message
        )