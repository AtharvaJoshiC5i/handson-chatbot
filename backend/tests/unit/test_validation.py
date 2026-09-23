"""Unit tests for NexaTel validation business logic."""

import pytest

from app.business.validation import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    require_parameter,
    validate_limit,
    validate_non_empty_string,
    validate_time_range,
)
from app.models.domain import TimeRange
from app.utils.errors import ValidationError


def test_validate_limit_defaults_when_missing() -> None:
    result = validate_limit(None)

    assert result == DEFAULT_LIMIT


def test_validate_limit_accepts_valid_value() -> None:
    result = validate_limit(5)

    assert result == 5


def test_validate_limit_accepts_maximum_value() -> None:
    result = validate_limit(MAX_LIMIT)

    assert result == MAX_LIMIT


def test_validate_limit_rejects_zero() -> None:
    with pytest.raises(ValidationError):
        validate_limit(0)


def test_validate_limit_rejects_negative_value() -> None:
    with pytest.raises(ValidationError):
        validate_limit(-1)


def test_validate_limit_rejects_value_above_maximum() -> None:
    with pytest.raises(ValidationError):
        validate_limit(MAX_LIMIT + 1)


def test_validate_limit_rejects_non_integer() -> None:
    with pytest.raises(ValidationError):
        validate_limit("10")  # type: ignore[arg-type]


def test_validate_time_range_accepts_supported_value() -> None:
    result = validate_time_range(
        TimeRange.CURRENT_MONTH,
    )

    assert result == TimeRange.CURRENT_MONTH


def test_validate_time_range_accepts_none_when_optional() -> None:
    result = validate_time_range(None)

    assert result is None


def test_validate_time_range_rejects_none_when_required() -> None:
    with pytest.raises(ValidationError):
        validate_time_range(
            None,
            required=True,
        )


def test_validate_time_range_rejects_invalid_value() -> None:
    with pytest.raises(ValidationError):
        validate_time_range("CURRENT_MONTH")  # type: ignore[arg-type]


def test_require_parameter_returns_value() -> None:
    parameters = {
        "time_range": TimeRange.CURRENT_MONTH,
    }

    result = require_parameter(
        parameters,
        "time_range",
    )

    assert result == TimeRange.CURRENT_MONTH


def test_require_parameter_rejects_missing_parameter() -> None:
    with pytest.raises(ValidationError):
        require_parameter(
            {},
            "time_range",
        )


def test_require_parameter_rejects_none_parameter() -> None:
    with pytest.raises(ValidationError):
        require_parameter(
            {"time_range": None},
            "time_range",
        )


def test_validate_non_empty_string_accepts_valid_value() -> None:
    result = validate_non_empty_string(
        "  CUST001  ",
        "customer_id",
    )

    assert result == "CUST001"


def test_validate_non_empty_string_rejects_empty_string() -> None:
    with pytest.raises(ValidationError):
        validate_non_empty_string(
            "",
            "customer_id",
        )


def test_validate_non_empty_string_rejects_whitespace() -> None:
    with pytest.raises(ValidationError):
        validate_non_empty_string(
            "   ",
            "customer_id",
        )


def test_validate_non_empty_string_rejects_non_string() -> None:
    with pytest.raises(ValidationError):
        validate_non_empty_string(
            123,
            "customer_id",
        )