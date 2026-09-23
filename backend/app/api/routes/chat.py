"""Chat API route for NexaTel."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_customer_context
from app.config.settings import get_settings
from app.database.connection import get_db
from app.llm.client import GroqLLMClient
from app.intent.router import IntentRouter
from app.models.api import ChatRequest, ChatResponse
from app.models.domain import CustomerContext
from app.services.chat_service import ChatService
from app.services.response_service import ResponseService
from app.utils.errors import LLMError, NexaTelError


router = APIRouter(
    prefix="/api",
    tags=["chat"],
)


def get_chat_service() -> ChatService:
    """Construct the chat service from the current application settings."""

    settings = get_settings()

    llm_client = GroqLLMClient(settings)

    return ChatService(
        llm_client=llm_client,
        intent_router=IntentRouter(),
        response_service=ResponseService(),
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
    customer: CustomerContext = Depends(
        get_customer_context
    ),
    db=Depends(get_db),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Process a NexaTel customer support message."""

    try:
        return service.process_message(
            db=db,
            customer=customer,
            message=request.message,
        )

    except LLMError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except NexaTelError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc