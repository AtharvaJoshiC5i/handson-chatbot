"""Validation and normalization of intent parameters."""

from __future__ import annotations

from typing import Any

from app.business.validation import (
    validate_limit,
)
from app.models.domain import (
    BillExtremeType,
    BillItemType,
    BillSortOrder,
    BillStatus,
    DeviceExtremeType,
    DeviceSortOrder,
    DeviceStatus,
    DeviceType,
    PaymentAggregateType,
    PaymentMethod,
    PaymentStatus,
    PlanType,
    SubscriptionStatus,
    SupportSortOrder,
    SupportTicketCategory,
    SupportTicketPriority,
    SupportTicketStatus,
    TimeRange,
    UsageExtremeType,
    UsagePercentageType,
    UsageType,
)
from app.models.llm import (
    IntentParameters,
)
from app.utils.errors import (
    ValidationError,
)


def _identifier(
    value: str,
    name: str,
) -> str:
    normalized = (
        value.strip()
    )

    if not normalized:
        raise ValidationError(
            f"Parameter '{name}' "
            "cannot be empty."
        )

    if len(normalized) > 150:
        raise ValidationError(
            f"Parameter '{name}' "
            "is too long."
        )

    return normalized


def normalize_parameters(
    parameters: IntentParameters,
) -> dict[str, Any]:
    normalized: dict[
        str,
        Any,
    ] = {}

    enum_fields = {
        "time_range": (
            TimeRange
        ),
        "usage_type": (
            UsageType
        ),
        "percentage_type": (
            UsagePercentageType
        ),
        "extreme_type": (
            UsageExtremeType
        ),
        "bill_extreme_type": (
            BillExtremeType
        ),
        "status_filter": (
            BillStatus
        ),
        "sort_order": (
            BillSortOrder
        ),
        "plan_type": (
            PlanType
        ),
        "subscription_status": (
            SubscriptionStatus
        ),
        "bill_item_type": (
            BillItemType
        ),
        "payment_status": (
            PaymentStatus
        ),
        "payment_method": (
            PaymentMethod
        ),
        "payment_aggregate_type": (
            PaymentAggregateType
        ),
        "ticket_status": (
            SupportTicketStatus
        ),
        "ticket_priority": (
            SupportTicketPriority
        ),
        "ticket_category": (
            SupportTicketCategory
        ),
        "support_sort_order": (
            SupportSortOrder
        ),
        "device_status": (
            DeviceStatus
        ),
        "device_type": (
            DeviceType
        ),
        "device_sort_order": (
            DeviceSortOrder
        ),
        "device_extreme_type": (
            DeviceExtremeType
        ),
    }

    for (
        field_name,
        enum_type,
    ) in enum_fields.items():
        value = getattr(
            parameters,
            field_name,
        )

        if value is None:
            continue

        if not isinstance(
            value,
            enum_type,
        ):
            raise ValidationError(
                f"Invalid {field_name} "
                "parameter."
            )

        normalized[
            field_name
        ] = value

    integer_fields = {
        "month": (
            parameters.month,
            1,
            12,
        ),
        "comparison_month": (
            parameters.comparison_month,
            1,
            12,
        ),
        "year": (
            parameters.year,
            2000,
            2100,
        ),
        "comparison_year": (
            parameters.comparison_year,
            2000,
            2100,
        ),
        "month_count": (
            parameters.month_count,
            1,
            12,
        ),
    }

    for (
        name,
        (
            value,
            minimum,
            maximum,
        ),
    ) in integer_fields.items():
        if value is None:
            continue

        if not (
            minimum
            <= value
            <= maximum
        ):
            raise ValidationError(
                f"Parameter '{name}' "
                "is outside the "
                "supported range."
            )

        normalized[
            name
        ] = value

    if (
        parameters.limit
        is not None
    ):
        normalized[
            "limit"
        ] = validate_limit(
            parameters.limit
        )

    if (
        parameters.minimum_amount
        is not None
    ):
        normalized[
            "minimum_amount"
        ] = float(
            parameters.minimum_amount
        )

    string_fields = (
        "current_bill_id",
        "previous_bill_id",
        "transaction_reference",
        "ticket_id",
        "device_id",
        "plan_id",
        "comparison_plan_id",
        "subscription_id",
    )

    for field_name in (
        string_fields
    ):
        value = getattr(
            parameters,
            field_name,
        )

        if value is not None:
            normalized[
                field_name
            ] = _identifier(
                value,
                field_name,
            )

    if (
        parameters.unresolved_only
        is not None
    ):
        normalized[
            "unresolved_only"
        ] = bool(
            parameters.unresolved_only
        )

    return normalized


def validate_required_parameters(
    *,
    intent_parameters: dict[
        str,
        Any,
    ],
    required_parameters: (
        set[str]
        | frozenset[str]
    ),
) -> None:
    missing = [
        parameter
        for parameter
        in required_parameters
        if intent_parameters.get(
            parameter
        )
        is None
    ]

    if missing:
        raise ValidationError(
            "Missing required "
            "parameter(s): "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )


def validate_allowed_parameters(
    *,
    intent_parameters: dict[
        str,
        Any,
    ],
    allowed_parameters: (
        set[str]
        | frozenset[str]
    ),
) -> None:
    unexpected = sorted(
        set(
            intent_parameters
        )
        - set(
            allowed_parameters
        )
    )

    if unexpected:
        raise ValidationError(
            "Parameter(s) not valid "
            "for this intent: "
            + ", ".join(
                unexpected
            )
        )