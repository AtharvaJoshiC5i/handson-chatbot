"""Groq LLM client for NexaTel."""

from __future__ import annotations

import json
import re
import time
from typing import Any

from openai import OpenAI
from openai import RateLimitError

from app.config.settings import Settings
from app.llm.prompts import SYSTEM_PROMPT
from app.models.domain import Intent, TimeRange
from app.models.llm import LLMIntentResponse
from app.models.llm import IntentParameters
from app.utils.errors import LLMError


COMPACT_SYSTEM_PROMPT = """
Classify the user's NexaTel support request. Return ONLY valid JSON in this
form: {"intent":"INTENT_NAME","parameters":{}}. For ambiguous requests,
use intent UNSUPPORTED and add a concise "clarification" question.

Allowed intents: GET_CURRENT_PLAN, GET_ACCOUNT_STATUS, GET_PLAN_RENEWAL,
GET_DATA_USAGE, GET_VOICE_USAGE, GET_CURRENT_BILL, GET_BILL_HISTORY,
GET_TOTAL_SPENDING, GET_BILL_COMPARISON, GET_PAYMENT_STATUS,
GET_PAYMENT_HISTORY, GET_SUPPORT_TICKETS, GET_DEVICE_INFORMATION, UNSUPPORTED.

For data or voice usage without a period, use
{"time_range":"CURRENT_MONTH"}. For history requests, use a numeric
{"limit":number} only when the user specifies one. For bill comparison,
extract explicit BILL IDs as current_bill_id and previous_bill_id.
""".strip()


def classify_deterministic_request(
    user_message: str,
) -> LLMIntentResponse | None:
    """Classify high-confidence requests without using the LLM."""

    normalized = user_message.lower().strip()
    parameters = IntentParameters()

    if (
        any(term in normalized for term in ("used", "usage", "consumption"))
        and not any(
            term in normalized
            for term in ("data", "gb", "voice", "minute", "call")
        )
    ):
        return LLMIntentResponse(
            intent=Intent.UNSUPPORTED,
            clarification=(
                "Do you mean your data usage or your voice/call-minute usage?"
            ),
        )

    if "plan" in normalized and any(
        term in normalized for term in ("bill", "invoice", "owe", "amount due")
    ):
        return LLMIntentResponse(
            intent=Intent.UNSUPPORTED,
            clarification=(
                "Do you mean your current plan or your current bill?"
            ),
        )

    limit_match = re.search(r"\b(?:last|first|top)\s+(\d+)\b", normalized)
    bill_ids = re.findall(r"\bbill\s*\d+\b", normalized, flags=re.IGNORECASE)
    if limit_match:
        parameters.limit = int(limit_match.group(1))
    if len(bill_ids) >= 2:
        parameters.current_bill_id = bill_ids[0].upper().replace(" ", "")
        parameters.previous_bill_id = bill_ids[1].upper().replace(" ", "")

    if "payment" in normalized or normalized == "payments":
        intent = (
            Intent.GET_PAYMENT_STATUS
            if any(
                term in normalized
                for term in (
                    "status",
                    "pending",
                    "successful",
                    "success",
                    "failed",
                    "fail",
                    "went through",
                    "gone through",
                )
            )
            else Intent.GET_PAYMENT_HISTORY
        )
    elif "compare" in normalized or "comparison" in normalized:
        intent = Intent.GET_BILL_COMPARISON
    elif (
        "support" in normalized
        or "ticket" in normalized
        or "case" in normalized
    ):
        intent = Intent.GET_SUPPORT_TICKETS
    elif "spend" in normalized or "spent" in normalized:
        intent = Intent.GET_TOTAL_SPENDING
    elif (
        "bill" in normalized
        or "invoice" in normalized
        or "owe" in normalized
        or "amount due" in normalized
    ):
        intent = (
            Intent.GET_BILL_HISTORY
            if "history" in normalized or "last" in normalized
            else Intent.GET_CURRENT_BILL
        )
    elif "data" in normalized or "gb" in normalized:
        intent = Intent.GET_DATA_USAGE
        parameters.time_range = (
            TimeRange.CURRENT_YEAR
            if "this year" in normalized or "current year" in normalized
            else TimeRange.LAST_MONTH
            if "last month" in normalized
            else TimeRange.CURRENT_MONTH
        )
    elif "minute" in normalized or "voice" in normalized or "call" in normalized:
        intent = Intent.GET_VOICE_USAGE
        parameters.time_range = (
            TimeRange.CURRENT_YEAR
            if "this year" in normalized or "current year" in normalized
            else TimeRange.LAST_MONTH
            if "last month" in normalized
            else TimeRange.CURRENT_MONTH
        )
    elif "renew" in normalized or "expiry" in normalized or "expire" in normalized:
        intent = Intent.GET_PLAN_RENEWAL
    elif "device" in normalized or "phone" in normalized or "router" in normalized:
        intent = Intent.GET_DEVICE_INFORMATION
    elif "plan" in normalized or "subscription" in normalized:
        intent = Intent.GET_CURRENT_PLAN
    elif (
        "account" in normalized
        or "status" in normalized
        or "active" in normalized
        or "suspended" in normalized
        or "cancelled" in normalized
    ):
        intent = Intent.GET_ACCOUNT_STATUS
    else:
        return None

    return LLMIntentResponse(intent=intent, parameters=parameters)


def classify_prompt_guard_request(
    user_message: str,
) -> LLMIntentResponse:
    """Classify requests when the configured model only returns guard scores."""

    return classify_deterministic_request(user_message) or LLMIntentResponse(
        intent=Intent.UNSUPPORTED,
    )


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

        deterministic_result = classify_deterministic_request(
            user_message
        )

        if deterministic_result is not None:
            return deterministic_result

        system_prompt = (
            COMPACT_SYSTEM_PROMPT
            if "prompt-guard" in self._model.lower()
            else SYSTEM_PROMPT
        )

        if "prompt-guard" in self._model.lower():
            return classify_prompt_guard_request(user_message)
        messages = (
            [
                {
                    "role": "user",
                    "content": (
                        f"{system_prompt}\n\n"
                        f"User request: {user_message}"
                    ),
                }
            ]
            if "prompt-guard" in self._model.lower()
            else [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ]
        )

        for attempt in range(3):
            try:
                response = self._client.chat.completions.create(
                    messages=messages,
                    model=self._model,
                    temperature=0,
                    max_tokens=256,
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
            content = response.choices[0].message.content

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