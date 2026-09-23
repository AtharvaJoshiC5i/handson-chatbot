from typing import Any

from app.models.domain import TruthStatus


class NexaTelError(Exception):
    """
    Base exception for expected application-level failures.
    """

    status: TruthStatus
    message: str
    details: dict[str, Any]

    def __init__(
        self,
        message: str,
        *,
        status: TruthStatus,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)

        self.message = message
        self.status = status
        self.details = details or {}


class ValidationError(NexaTelError):
    """Raised when application-level validation fails."""

    def __init__(
        self,
        message: str = "The supplied information is invalid.",
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status=TruthStatus.VALIDATION_ERROR,
            details=details,
        )


class AccessDeniedError(NexaTelError):
    """Raised when a customer is not authorized to access a resource."""

    def __init__(
        self,
        message: str = "You are not authorized to access that information.",
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status=TruthStatus.ACCESS_DENIED,
            details=details,
        )


class UnsupportedIntentError(NexaTelError):
    """Raised when a request maps to an unsupported capability."""

    def __init__(
        self,
        message: str = (
            "I currently can't answer that using the available "
            "NexaTel customer data."
        ),
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status=TruthStatus.UNSUPPORTED,
            details=details,
        )


class AmbiguousRequestError(NexaTelError):
    """Raised when a request cannot be safely interpreted."""

    def __init__(
        self,
        message: str = (
            "I need a little more information to answer that accurately."
        ),
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status=TruthStatus.AMBIGUOUS,
            details=details,
        )


class ResourceNotFoundError(NexaTelError):
    """Raised when the requested authoritative data does not exist."""

    def __init__(
        self,
        message: str = (
            "I don't have that information available in the "
            "NexaTel customer data."
        ),
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status=TruthStatus.NOT_FOUND,
            details=details,
        )


class DatabaseError(NexaTelError):
    """Raised when an expected database operation fails."""

    def __init__(
        self,
        message: str = "The customer data could not be retrieved.",
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status=TruthStatus.DATABASE_ERROR,
            details=details,
        )


class LLMError(NexaTelError):
    """Raised when the LLM service cannot provide a valid result."""

    def __init__(
        self,
        message: str = "The language processing service is unavailable.",
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status=TruthStatus.VALIDATION_ERROR,
            details=details,
        )