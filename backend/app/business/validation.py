"""Business-level validation for NexaTel requests."""

from __future__ import annotations

from typing import Any

from app.models.domain import TimeRange
from app.utils.errors import ValidationError


DEFAULT_LIMIT = 10
MAX_LIMIT = 20


def validate_limit(limit: int | None) -> int:
    """Validate and normalize a list-result limit."""

    if limit is None:
        return DEFAULT_LIMIT

    if not isinstance(limit, int):
        raise ValidationError("Limit must be an integer.")

    if limit < 1:
        raise ValidationError("Limit must be at least 1.")

    if limit > MAX_LIMIT:
        raise ValidationError(
            f"Limit cannot exceed {MAX_LIMIT}."
        )

    return limit


def validate_time_range(
    time_range: TimeRange | None,
    *,
    required: bool = False,
) -> TimeRange | None:
    """Validate an optional or required time range."""

    if time_range is None:
        if required:
            raise ValidationError(
                "A supported time range is required for this request."
            )

        return None

    if not isinstance(time_range, TimeRange):
        raise ValidationError("Invalid time range.")

    return time_range


def require_parameter(
    parameters: dict[str, Any],
    parameter_name: str,
) -> Any:
    """Return a required parameter or raise a validation error."""

    value = parameters.get(parameter_name)

    if value is None:
        raise ValidationError(
            f"Required parameter '{parameter_name}' is missing."
        )

    return value


def validate_non_empty_string(
    value: Any,
    parameter_name: str,
) -> str:
    """Validate a required non-empty string parameter."""

    if not isinstance(value, str):
        raise ValidationError(
            f"Parameter '{parameter_name}' must be a string."
        )

    normalized = value.strip()

    if not normalized:
        raise ValidationError(
            f"Parameter '{parameter_name}' cannot be empty."
        )

    return normalized