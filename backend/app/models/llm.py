"""Pydantic models for LLM structured outputs."""

from __future__ import annotations

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.models.domain import (
    BillExtremeType,
    BillSortOrder,
    BillStatus,
    DeviceExtremeType,
    DeviceSortOrder,
    DeviceStatus,
    DeviceType,
    Intent,
    PaymentAggregateType,
    PaymentMethod,
    PaymentStatus,
    SupportSortOrder,
    SupportTicketCategory,
    SupportTicketPriority,
    SupportTicketStatus,
    TimeRange,
    UsageExtremeType,
    UsagePercentageType,
    UsageType,
)


class IntentOption(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    label: str = Field(
        min_length=1,
        max_length=80,
    )

    message: str = Field(
        min_length=1,
        max_length=4000,
    )


class IntentParameters(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    # Shared period parameters.
    time_range: (
        TimeRange | None
    ) = None

    month: int | None = Field(
        default=None,
        ge=1,
        le=12,
    )

    year: int | None = Field(
        default=None,
        ge=2000,
        le=2100,
    )

    comparison_month: (
        int | None
    ) = Field(
        default=None,
        ge=1,
        le=12,
    )

    comparison_year: (
        int | None
    ) = Field(
        default=None,
        ge=2000,
        le=2100,
    )

    month_count: (
        int | None
    ) = Field(
        default=None,
        ge=1,
        le=12,
    )

    limit: int | None = Field(
        default=None,
        ge=1,
        le=20,
    )

    # Phase 1 — usage.
    usage_type: (
        UsageType | None
    ) = None

    percentage_type: (
        UsagePercentageType | None
    ) = None

    extreme_type: (
        UsageExtremeType | None
    ) = None

    # Phase 2 — billing.
    current_bill_id: (
        str | None
    ) = None

    previous_bill_id: (
        str | None
    ) = None

    bill_extreme_type: (
        BillExtremeType | None
    ) = None

    status_filter: (
        BillStatus | None
    ) = None

    minimum_amount: (
        float | None
    ) = Field(
        default=None,
        ge=0,
    )

    sort_order: (
        BillSortOrder | None
    ) = None

    # Phase 3 — payments.
    payment_status: (
        PaymentStatus | None
    ) = None

    payment_method: (
        PaymentMethod | None
    ) = None

    transaction_reference: (
        str | None
    ) = None

    payment_aggregate_type: (
        PaymentAggregateType | None
    ) = None

    # Phase 4 — support.
    ticket_id: (
        str | None
    ) = None

    ticket_status: (
        SupportTicketStatus | None
    ) = None

    ticket_priority: (
        SupportTicketPriority | None
    ) = None

    ticket_category: (
        SupportTicketCategory | None
    ) = None

    unresolved_only: (
        bool | None
    ) = None

    support_sort_order: (
        SupportSortOrder | None
    ) = None

    # Phase 4 — devices.
    device_id: (
        str | None
    ) = None

    device_status: (
        DeviceStatus | None
    ) = None

    device_type: (
        DeviceType | None
    ) = None

    device_sort_order: (
        DeviceSortOrder | None
    ) = None

    device_extreme_type: (
        DeviceExtremeType | None
    ) = None


class LLMIntentResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    intent: Intent

    parameters: IntentParameters = (
        Field(
            default_factory=(
                IntentParameters
            ),
        )
    )

    clarification: (
        str | None
    ) = None

    options: list[
        IntentOption
    ] = Field(
        default_factory=list,
        max_length=8,
    )