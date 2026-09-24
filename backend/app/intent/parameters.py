"""Validation and normalization of intent parameters."""

from __future__ import annotations

from typing import Any

from app.business.validation import validate_limit
from app.models.domain import TimeRange
from app.models.llm import IntentParameters
from app.utils.errors import ValidationError


def _validate_identifier(
    value: str | None,
    parameter_name: str,
) -> str:
    """Validate a backend resource identifier."""

    if value is None:
        raise ValidationError(
            f"Parameter '{parameter_name}' is required."
        )

    if not isinstance(value, str):
        raise ValidationError(
            f"Parameter '{parameter_name}' must be a string."
        )

    normalized = value.strip()

    if not normalized:
        raise ValidationError(
            f"Parameter '{parameter_name}' cannot be empty."
        )

    if len(normalized) > 100:
        raise ValidationError(
            f"Parameter '{parameter_name}' is too long."
        )

    return normalized


def normalize_parameters(
    parameters: IntentParameters,
) -> dict[str, Any]:
    """Convert LLM parameters into validated backend parameters.

    The resulting dictionary is safe for the intent router to consume.

    This function does not perform database operations.
    """

    normalized: dict[str, Any] = {}

    if parameters.time_range is not None:
        if not isinstance(parameters.time_range, TimeRange):
            raise ValidationError(
                "Invalid time range parameter."
            )

        normalized["time_range"] = parameters.time_range

    if parameters.limit is not None:
        normalized["limit"] = validate_limit(
            parameters.limit
        )

    if parameters.current_bill_id is not None:
        normalized["current_bill_id"] = _validate_identifier(
            parameters.current_bill_id,
            "current_bill_id",
        )

    if parameters.previous_bill_id is not None:
        normalized["previous_bill_id"] = _validate_identifier(
            parameters.previous_bill_id,
            "previous_bill_id",
        )

    return normalized


def validate_required_parameters(
    *,
    intent_parameters: dict[str, Any],
    required_parameters: set[str] | frozenset[str],
) -> None:
    """Ensure all parameters required by an intent are present."""

    missing = [
        parameter
        for parameter in required_parameters
        if parameter not in intent_parameters
        or intent_parameters[parameter] is None
    ]

    if missing:
        raise ValidationError(
            "Missing required parameter(s): "
            + ", ".join(sorted(missing))
        )


def validate_allowed_parameters(
    *,
    intent_parameters: dict[str, Any],
    allowed_parameters: set[str] | frozenset[str],
) -> None:
    """Reject parameters that do not belong to the selected intent."""

    unexpected = sorted(
        set(intent_parameters) - set(allowed_parameters)
    )

    if unexpected:
        raise ValidationError(
            "Parameter(s) not valid for this intent: "
            + ", ".join(unexpected)
        )