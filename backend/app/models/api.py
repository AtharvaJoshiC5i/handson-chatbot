"""Pydantic models for NexaTel API requests and responses."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """Incoming chat request."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )


class ChatResponse(BaseModel):
    """Public chat response."""

    model_config = ConfigDict(extra="forbid")

    message: str
    status: str
    source: str | None = None


class HealthResponse(BaseModel):
    """Health-check response."""

    model_config = ConfigDict(extra="forbid")

    status: str
    environment: str


class ErrorResponse(BaseModel):
    """Standard API error response."""

    model_config = ConfigDict(extra="forbid")

    error: str
    message: str
    request_id: str | None = None


class DebugChatResponse(BaseModel):
    """Development-only debug response."""

    model_config = ConfigDict(extra="forbid")

    response: ChatResponse
    intent: str | None = None
    parameters: dict[str, object] | None = None