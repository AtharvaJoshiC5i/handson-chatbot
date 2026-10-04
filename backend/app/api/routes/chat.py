"""Chat API route."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    status,
)
from fastapi.responses import StreamingResponse

from app.config.settings import (
    Settings,
    get_settings,
)
from app.database.connection import get_db
from app.database.queries.customers import (
    get_customer,
    list_demo_customers,
)
from app.services.account_snapshot_service import (
    build_account_snapshot,
)
from app.llm.client import GroqLLMClient
from app.models.api import (
    AccountSnapshotResponse,
    ChatRequest,
    ChatResponse,
    ConversationResetRequest,
    CustomerProfileResponse,
    DemoCustomerItem,
    DemoCustomersResponse,
)
from app.models.domain import CustomerContext
from app.services.chat_service import ChatService
from app.services.conversation_service import ConversationService
from app.utils.errors import LLMError


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


def _sse_event(
    event: str,
    data: dict[str, object],
) -> str:
    return (
        f"event: {event}\n"
        f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    )

conversation_service = ConversationService()


def get_customer_context(
    x_customer_id: str = Header(
        ...,
        alias="X-Customer-ID",
    ),
) -> CustomerContext:
    """
    Build the trusted customer context from the request header.

    Customer identity is taken from X-Customer-ID rather than
    from free text inside the user's message.
    """

    try:
        return CustomerContext(
            customer_id=x_customer_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid customer ID.",
        ) from exc


@router.get(
    "/profile",
    response_model=CustomerProfileResponse,
)
def get_selected_customer_profile(
    customer: CustomerContext = Depends(
        get_customer_context
    ),
    db: sqlite3.Connection = Depends(
        get_db
    ),
) -> CustomerProfileResponse:
    """Return only the authenticated selected customer's display name."""

    try:
        row = get_customer(
            db,
            customer_id=customer.customer_id,
        )
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Customer profile is unavailable.",
        ) from exc

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer account was not found.",
        )

    phone = row["phone"]
    phone_masked = (
        f"{phone[:-4]}****"
        if len(phone) >= 4
        else phone
    )

    return CustomerProfileResponse(
        name=row["name"],
        phone_masked=phone_masked,
        city=row["city"],
        service_address_line=row[
            "service_address_line"
        ]
        if "service_address_line" in row.keys()
        else "",
        account_status=row["account_status"],
    )


def _mask_phone(phone: str) -> str:
    if len(phone) < 4:
        return phone
    return f"{phone[:-4]}****"


@router.get(
    "/demo-customers",
    response_model=DemoCustomersResponse,
)
def get_demo_customers(
    db: sqlite3.Connection = Depends(
        get_db
    ),
) -> DemoCustomersResponse:
    """List demo accounts for the frontend account switcher."""

    try:
        rows = list_demo_customers(db)
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Demo customers are unavailable.",
        ) from exc

    return DemoCustomersResponse(
        customers=[
            DemoCustomerItem(
                customer_id=row["customer_id"],
                name=row["name"],
                phone_masked=_mask_phone(
                    row["phone"],
                ),
            )
            for row in rows
        ],
    )


@router.get(
    "/account-snapshot",
    response_model=AccountSnapshotResponse,
)
def get_account_snapshot(
    customer: CustomerContext = Depends(
        get_customer_context
    ),
    db: sqlite3.Connection = Depends(
        get_db
    ),
) -> AccountSnapshotResponse:
    """Return aggregated account context for personalization."""

    try:
        snapshot = build_account_snapshot(
            db,
            customer.customer_id,
        )
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account snapshot is unavailable.",
        ) from exc

    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer account was not found.",
        )

    return AccountSnapshotResponse.model_validate(
        snapshot,
    )


@router.post(
    "",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
    customer: CustomerContext = Depends(
        get_customer_context
    ),
    db: sqlite3.Connection = Depends(
        get_db
    ),
    settings: Settings = Depends(
        get_settings
    ),
) -> ChatResponse:
    """
    Process one NexaTel customer-support chat request.
    """

    try:
        llm_client = GroqLLMClient(
            settings
        )

        service = ChatService(
            llm_client,
            conversation_service=conversation_service,
        )

        return service.respond(
            db=db,
            customer=customer,
            user_message=request.message,
            conversation_id=request.conversation_id,
        )

    except LLMError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=str(exc),
        ) from exc


@router.post("/stream")
def chat_stream(
    request: ChatRequest,
    customer: CustomerContext = Depends(
        get_customer_context
    ),
    db: sqlite3.Connection = Depends(
        get_db
    ),
    settings: Settings = Depends(
        get_settings
    ),
) -> StreamingResponse:
    """Stream the final LLM wording after backend processing completes."""

    try:
        service = ChatService(
            GroqLLMClient(settings),
            conversation_service=conversation_service,
        )
        metadata, text_stream = service.respond_stream(
            db=db,
            customer=customer,
            user_message=request.message,
            conversation_id=request.conversation_id,
        )
    except LLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    def events() -> Iterator[str]:
        yield _sse_event(
            "metadata",
            metadata.model_dump(mode="json"),
        )

        try:
            for text_delta in text_stream:
                if text_delta:
                    yield _sse_event(
                        "delta",
                        {"text": text_delta},
                    )

            yield _sse_event("done", {})
        except LLMError as exc:
            yield _sse_event(
                "error",
                {"message": str(exc)},
            )

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/reset")
def reset_conversation(
    request: ConversationResetRequest,
    customer: CustomerContext = Depends(
        get_customer_context
    ),
) -> dict[str, str]:
    """Clear the requesting customer's ephemeral conversation state."""

    conversation_service.clear(
        request.conversation_id,
        customer,
    )
    return {
        "status": "cleared"
    }