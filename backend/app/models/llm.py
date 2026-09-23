"""Pydantic models for LLM structured outputs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.domain import Intent, TimeRange


class IntentParameters(BaseModel):
    """Parameters extracted by the LLM.

    These values are untrusted until validated by the backend.
    """

    model_config = ConfigDict(extra="forbid")

    time_range: TimeRange | None = None

    limit: int | None = Field(
        default=None,
        ge=1,
        le=20,
    )

    current_bill_id: str | None = None

    previous_bill_id: str | None = None


class LLMIntentResponse(BaseModel):
    """Strict structured intent returned by the LLM."""

    model_config = ConfigDict(extra="forbid")

    intent: Intent
    parameters: IntentParameters = Field(
        default_factory=IntentParameters,
    )