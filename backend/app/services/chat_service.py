"""Top-level NexaTel chat orchestration."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from uuid import uuid4

from app.llm.client import GroqLLMClient
from app.llm.extractor import IntentExtractor
from app.models.api import (
    ChatOption,
    ChatResponse,
)
from app.models.domain import (
    CustomerContext,
)
from app.services.presentation_service import (
    PresentationService,
)
from app.services.conversation_service import (
    ConversationService,
)
from app.services.response_service import (
    ResponseService,
)
from app.services.structured_data_service import (
    StructuredDataService,
)
from app.truth.result import TruthResult
from app.utils.errors import LLMError


_DEFAULT_CONVERSATION_SERVICE = ConversationService()


class ChatService:
    """Coordinate intent extraction, truth retrieval and presentation."""

    def __init__(
        self,
        llm_client: GroqLLMClient,
        conversation_service: ConversationService | None = None,
    ) -> None:
        self._llm_client = llm_client
        self._conversation_service = (
            conversation_service
            or _DEFAULT_CONVERSATION_SERVICE
        )

        self._intent_extractor = (
            IntentExtractor(
                llm_client
            )
        )

        from app.intent.router import (
            IntentRouter,
        )

        self._structured_data_service = (
            StructuredDataService(
                intent_extractor=(
                    self._intent_extractor
                ),
                intent_router=(
                    IntentRouter()
                ),
            )
        )

        self._response_service = (
            ResponseService()
        )

        self._presentation_service = (
            PresentationService()
        )

    def respond(
        self,
        *,
        db: sqlite3.Connection,
        customer: CustomerContext,
        user_message: str,
        conversation_id: str | None = None,
    ) -> ChatResponse:
        """
        Process one chat turn.

        The same verified TruthResult is used for both readable text
        and optional structured presentation.
        """

        truth_result, options = self._process_turn(
            db=db,
            customer=customer,
            user_message=user_message,
            conversation_id=conversation_id,
        )

        return self._build_chat_response(
            truth_result=truth_result,
            options=options,
        )

    def respond_stream(
        self,
        *,
        db: sqlite3.Connection,
        customer: CustomerContext,
        user_message: str,
        conversation_id: str | None = None,
    ) -> tuple[ChatResponse, Iterator[str]]:
        """Resolve a turn on the backend and stream only its final wording."""

        truth_result, options = self._process_turn(
            db=db,
            customer=customer,
            user_message=user_message,
            conversation_id=conversation_id,
        )
        backend_output = self._response_service.build_response(
            truth_result
        )
        metadata = self._build_chat_response(
            truth_result=truth_result,
            options=options,
            message_override="",
        )

        generate_response_stream = getattr(
            self._llm_client,
            "generate_response_stream",
            None,
        )
        if callable(generate_response_stream):
            text_stream = generate_response_stream(backend_output)

            def stream_with_backend_fallback() -> Iterator[str]:
                received_text = False
                try:
                    for delta in text_stream:
                        received_text = True
                        yield delta
                except LLMError:
                    if received_text:
                        raise
                    yield backend_output

            return metadata, stream_with_backend_fallback()

        generate_response = getattr(
            self._llm_client,
            "generate_response",
            None,
        )
        try:
            final_message = (
                generate_response(backend_output)
                if callable(generate_response)
                else backend_output
            )
        except LLMError:
            final_message = backend_output

        return metadata, iter((final_message,))

    def _process_turn(
        self,
        *,
        db: sqlite3.Connection,
        customer: CustomerContext,
        user_message: str,
        conversation_id: str | None,
    ) -> tuple[TruthResult, list[ChatOption]]:
        conversation_id = conversation_id or uuid4().hex
        context = self._conversation_service.get_context(
            conversation_id,
            customer,
        )
        intent_response = self._conversation_service.resolve_followup(
            user_message,
            context,
        )
        intent_response, truth_result = self._structured_data_service.execute(
            db=db,
            customer=customer,
            user_message=user_message,
            intent_response=intent_response,
            context_hint=context.compact_hint(),
        )
        context.update(intent_response, truth_result)
        options = [
            ChatOption(
                label=option.label,
                message=option.message,
            )
            for option in intent_response.options
        ]
        return truth_result, options

    def _build_chat_response(
        self,
        *,
        truth_result: TruthResult,
        options: list[ChatOption],
        message_override: str | None = None,
    ) -> ChatResponse:
        backend_output = (
            self._response_service
            .build_response(
                truth_result
            )
        )
        generate_response = getattr(
            self._llm_client,
            "generate_response",
            None,
        )
        message = message_override
        if message is None:
            try:
                message = (
                    generate_response(backend_output)
                    if callable(generate_response)
                    else backend_output
                )
            except LLMError:
                message = backend_output

        presentation = (
            self._presentation_service
            .build(
                truth_result
            )
        )

        source = None

        if (
            truth_result.source
            is not None
        ):
            source = (
                truth_result
                .source
                .source_name
            )

        return ChatResponse(
            message=message,
            status=(
                truth_result
                .status
                .value
            ),
            source=source,
            presentation=presentation,
            options=options,
        )