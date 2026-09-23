from fastapi import Header, HTTPException, status

from app.models.domain import CustomerContext


CUSTOMER_ID_HEADER = "X-Customer-ID"


def get_customer_context(
    customer_id: str | None = Header(
        default=None,
        alias=CUSTOMER_ID_HEADER,
    ),
) -> CustomerContext:
    """
    Extract the authenticated development customer context.

    Phase 1 uses X-Customer-ID as the POC authentication mechanism.

    The customer identity comes from the request context and is never
    obtained from the LLM or from the user's natural-language message.
    """

    if customer_id is None or not customer_id.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer context is required.",
        )

    try:
        return CustomerContext(customer_id=customer_id.strip())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc