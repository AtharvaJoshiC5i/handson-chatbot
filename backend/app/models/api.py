"""Pydantic models for NexaTel API requests and responses."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """Incoming chat request."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )
    conversation_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
    )


class ConversationResetRequest(BaseModel):
    """Request to clear one customer's ephemeral conversation context."""

    model_config = ConfigDict(extra="forbid")

    conversation_id: str = Field(
        min_length=1,
        max_length=128,
    )


class ChatOption(BaseModel):
    """Selectable follow-up question."""

    model_config = ConfigDict(extra="forbid")

    label: str
    message: str


class KeyValueItem(BaseModel):
    """One label/value pair."""

    model_config = ConfigDict(extra="forbid")

    label: str
    value: str


class KeyValuePresentation(BaseModel):
    """Compact structured key/value result."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["key_value"] = "key_value"
    title: str | None = None
    items: list[KeyValueItem]


class ComparisonColumn(BaseModel):
    """One comparison column."""

    model_config = ConfigDict(extra="forbid")

    key: str
    label: str


class ComparisonRow(BaseModel):
    """One comparison metric."""

    model_config = ConfigDict(extra="forbid")

    label: str
    values: dict[str, str]


class ComparisonPresentation(BaseModel):
    """Side-by-side comparison result."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["comparison"] = "comparison"
    title: str | None = None
    columns: list[ComparisonColumn]
    rows: list[ComparisonRow]


class ListItem(BaseModel):
    """One structured list entry."""

    model_config = ConfigDict(extra="forbid")

    label: str
    value: str
    detail: str | None = None


class ListPresentation(BaseModel):
    """Compact structured list."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["list"] = "list"
    title: str | None = None
    items: list[ListItem]


class TableColumn(BaseModel):
    """Table column definition."""

    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    align: Literal["left", "right"] = "left"


class TablePresentation(BaseModel):
    """Compact table-like response."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["table"] = "table"
    title: str | None = None
    columns: list[TableColumn]
    rows: list[dict[str, str]]


class TimeSeriesPoint(BaseModel):
    """One chronological numeric value for a chart and its data table."""

    model_config = ConfigDict(extra="forbid")

    period: str
    value: float
    detail: str | None = None


class TimeSeriesPresentation(BaseModel):
    """Validated numeric series for usage or billing visualizations."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["time_series"] = "time_series"
    title: str | None = None
    chart_type: Literal["line", "bar"]
    unit: str
    value_format: Literal["number", "inr"] = "number"
    points: list[TimeSeriesPoint] = Field(min_length=2)


class SummarySection(BaseModel):
    """One cross-domain summary section."""

    model_config = ConfigDict(extra="forbid")

    label: str
    primary: str
    secondary: str | None = None


class SummaryPresentation(BaseModel):
    """Compact multi-domain summary."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["summary"] = "summary"
    title: str | None = None
    sections: list[SummarySection]


class Customer360Table(BaseModel):
    """All records for one customer-owned domain table."""

    model_config = ConfigDict(extra="forbid")

    title: str
    columns: list[TableColumn]
    rows: list[dict[str, str]]


class Customer360Presentation(BaseModel):
    """Customer 360 highlights plus complete related records."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["customer_360"] = "customer_360"
    title: str | None = None
    sections: list[SummarySection]
    tables: list[Customer360Table]


ChatPresentation = (
    KeyValuePresentation
    | ComparisonPresentation
    | ListPresentation
    | TablePresentation
    | TimeSeriesPresentation
    | SummaryPresentation
    | Customer360Presentation
)


class ChatResponse(BaseModel):
    """Public chat response."""

    model_config = ConfigDict(extra="forbid")

    message: str
    status: str
    source: str | None = None

    presentation: ChatPresentation | None = Field(
        default=None,
        discriminator="type",
    )

    options: list[ChatOption] = Field(
        default_factory=list
    )


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