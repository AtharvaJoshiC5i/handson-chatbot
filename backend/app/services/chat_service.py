"""Main chat orchestration service for NexaTel."""

from __future__ import annotations

import sqlite3

from app.llm.client import GroqLLMClient
from app.llm.extractor import IntentExtractor
from app.intent.router import IntentRouter
from app.models.api import ChatOption, ChatResponse
from app.models.domain import CustomerContext
from app.services.response_service import ResponseService
from app.services.structured_data_service import StructuredDataService
from app.truth.result import TruthResult
from app.utils.errors import NexaTelError


class ChatService:
    """Coordinate LLM intent extraction and backend execution."""

    def __init__(
        self,
        *,
        llm_client: GroqLLMClient,
        intent_router: IntentRouter,
        response_service: ResponseService,
    ) -> None:
        self._structured_data_service = (
            StructuredDataService(
                intent_extractor=IntentExtractor(
                    llm_client
                ),
                intent_router=intent_router,
            )
        )

        self._response_service = response_service

    def process_message(
        self,
        *,
        db: sqlite3.Connection,
        customer: CustomerContext,
        message: str,
    ) -> ChatResponse:
        """Process a customer chat message."""

        try:
            llm_intent, truth_result = (
                self._structured_data_service.execute(
                    db=db,
                    customer=customer,
                    user_message=message,
                )
            )

            response_text = (
                self._response_service.build_response(
                    truth_result
                )
            )

            return self._build_chat_response(
                truth_result=truth_result,
                response_text=response_text,
                options=(
                    [
                        ChatOption(
                            label=option.label,
                            message=option.message,
                        )
                        for option in llm_intent.options
                    ]
                    if truth_result.status.value == "AMBIGUOUS"
                    else []
                ),
            )

        except NexaTelError:
            raise

    @staticmethod
    def _build_chat_response(
        *,
        truth_result: TruthResult,
        response_text: str,
        options: list[ChatOption],
    ) -> ChatResponse:
        """Build the public API response."""

        return ChatResponse(
            message=response_text,
            status=truth_result.status.value,
            source=(
                truth_result.source.source_name
                if truth_result.source
                else None
            ),
            options=options,
        )