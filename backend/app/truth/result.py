"""Truth result primitives for NexaTel."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.models.domain import TruthSource, TruthStatus


T = TypeVar("T")


class TruthResult(BaseModel, Generic[T]):
    """Verified or explicitly classified backend result."""

    model_config = ConfigDict(extra="forbid")

    status: TruthStatus
    data: T | None = None
    source: TruthSource | None = None
    message: str | None = None
    metadata: dict[str, str] = Field(
        default_factory=dict
    )

    @property
    def is_verified(self) -> bool:
        """Return whether this result contains verified backend data."""

        return (
            self.status == TruthStatus.VERIFIED
            and self.data is not None
            and self.source is not None
        )


def verified_result(
    data: T,
    *,
    source: TruthSource,
    message: str | None = None,
    metadata: dict[str, str] | None = None,
) -> TruthResult[T]:
    """Create a verified backend result."""

    return TruthResult(
        status=TruthStatus.VERIFIED,
        data=data,
        source=source,
        message=message,
        metadata=metadata or {},
    )


def not_found_result(
    *,
    source: TruthSource | None = None,
    message: str = "No matching data was found.",
) -> TruthResult[None]:
    """Create a NOT_FOUND result."""

    return TruthResult(
        status=TruthStatus.NOT_FOUND,
        source=source,
        message=message,
    )


def ambiguous_result(
    *,
    message: str,
    source: TruthSource | None = None,
) -> TruthResult[None]:
    """Create an AMBIGUOUS result."""

    return TruthResult(
        status=TruthStatus.AMBIGUOUS,
        source=source,
        message=message,
    )


def unsupported_result(
    *,
    message: str,
) -> TruthResult[None]:
    """Create an UNSUPPORTED result."""

    return TruthResult(
        status=TruthStatus.UNSUPPORTED,
        message=message,
    )


def validation_error_result(
    *,
    message: str,
) -> TruthResult[None]:
    """Create a VALIDATION_ERROR result."""

    return TruthResult(
        status=TruthStatus.VALIDATION_ERROR,
        message=message,
    )


def access_denied_result(
    *,
    message: str = "Access denied.",
) -> TruthResult[None]:
    """Create an ACCESS_DENIED result."""

    return TruthResult(
        status=TruthStatus.ACCESS_DENIED,
        message=message,
    )


def database_error_result(
    *,
    message: str = "The database could not be accessed.",
) -> TruthResult[None]:
    """Create a DATABASE_ERROR result."""

    return TruthResult(
        status=TruthStatus.DATABASE_ERROR,
        message=message,
    )