"""Intent extraction service."""

from __future__ import annotations

from inspect import Parameter, signature

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
        *,
        context_hint: str | None = None,
    ) -> LLMIntentResponse:
        """Extract and validate a structured intent."""

        extract_intent = (
            self._llm_client.extract_intent
        )

        if not context_hint:
            return extract_intent(
                user_message
            )

        parameters = signature(
            extract_intent
        ).parameters.values()

        supports_context = any(
            parameter.name == "context_hint"
            or parameter.kind
            == Parameter.VAR_KEYWORD
            for parameter in parameters
        )

        if not supports_context:
            return extract_intent(
                user_message
            )

        return extract_intent(
            user_message,
            context_hint=context_hint,
        )