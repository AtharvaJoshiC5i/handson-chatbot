"""Groq LLM client for NexaTel."""

from __future__ import annotations

import json
import time
from typing import Any

from openai import OpenAI
from openai import RateLimitError

from app.config.settings import Settings
from app.llm.prompts import SYSTEM_PROMPT
from app.models.llm import LLMIntentResponse
from app.utils.errors import LLMError


class GroqLLMClient:
    """Thin provider adapter around the Groq API.

    This class is intentionally isolated from business logic,
    database access, and authorization.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            raise LLMError(
                "GROQ_API_KEY is not configured."
            )

        self._client = OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )

        self._model = settings.groq_model

        self._timeout = settings.llm_timeout_seconds

    def extract_intent(
        self,
        user_message: str,
    ) -> LLMIntentResponse:
        """Extract a structured NexaTel intent from user text."""

        for attempt in range(3):
            try:
                response = self._client.responses.create(
                    input=(
                        f"{SYSTEM_PROMPT}\n\n"
                        "User message:\n"
                        f"{user_message}"
                    ),
                    model=self._model,
                    temperature=0,
                    timeout=self._timeout,
                )
                break
            except RateLimitError as exc:
                if attempt == 2:
                    raise LLMError(
                        "The language model rate limit was exceeded."
                    ) from exc

                time.sleep(2 ** attempt)
            except Exception as exc:
                raise LLMError(
                    "The language model could not process the request."
                ) from exc

        try:
            content = response.output_text

            if not content:
                raise ValueError(
                    "Groq returned an empty response."
                )

            payload: dict[str, Any] = json.loads(content)

            if isinstance(payload.get("intent"), str):
                payload["intent"] = payload["intent"].upper()

            parameters = payload.get("parameters")

            if not isinstance(parameters, dict):
                parameters = {}
                payload["parameters"] = parameters

            for parameter_name in (
                "time_range",
                "limit",
                "current_bill_id",
                "previous_bill_id",
            ):
                if parameter_name in payload:
                    parameters[parameter_name] = payload.pop(
                        parameter_name
                    )

            if isinstance(parameters, dict):
                time_range = parameters.get("time_range")

                if isinstance(time_range, str):
                    parameters["time_range"] = time_range.upper()

            return LLMIntentResponse.model_validate(
                payload
            )

        except Exception as exc:
            raise LLMError(
                "The language model returned an invalid "
                "structured response."
            ) from exc