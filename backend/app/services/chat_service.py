"""Top-level NexaTel chat orchestration."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from uuid import uuid4

from app.config.settings import get_settings
from app.llm.client import GroqLLMClient
from app.llm.extractor import IntentExtractor
from app.models.api import (
    ChatOption,
    ChatPresentation,
    ChatResponse,
    ChoiceListPresentation,
    PresentationMeta,
)
from app.models.domain import (
    CustomerContext,
    TruthStatus,
)
from app.services.conversation_service import (
    ConversationService,
)
from app.services.presentation_service import (
    PresentationService,
)
from app.services.response_narrative_policy import (
    rewrite_max_tokens,
    should_skip_response_rewrite,
)
from app.services.response_service import (
    ResponseService,
)
from app.services.response_turn_metrics import (
    log_response_turn,
)
from app.services.chat_history_service import (
    ChatHistoryService,
)
from app.services.conversation_context_store import (
    save_conversation_context,
)
from app.services.structured_data_service import (
    StructuredDataService,
)
from app.truth.result import TruthResult
from app.utils.errors import LLMError


_DEFAULT_CONVERSATION_SERVICE = ConversationService()
_DEFAULT_CHAT_HISTORY_SERVICE = ChatHistoryService()


def _narrative_profile(
    result_type: str | None,
) -> str:
    if result_type == "CUSTOMER_360":
        return "customer_360"

    return "default"


def _presentation_meta_from_truth(
    truth_result: TruthResult,
) -> PresentationMeta | None:
    data = truth_result.data
    if not isinstance(data, dict):
        return None

    period = data.get("period")
    if isinstance(period, str) and period.strip():
        scope = data.get("plan_type")
        scope_label = (
            str(scope).strip()
            if isinstance(scope, str) and scope.strip()
            else None
        )
        return PresentationMeta(
            period_label=period.strip(),
            scope_label=scope_label,
        )

    billing_period = data.get("billing_period")
    if isinstance(billing_period, str) and billing_period.strip():
        return PresentationMeta(
            period_label=billing_period.strip(),
        )

    bill = data.get("bill")
    if isinstance(bill, dict):
        bill_period = bill.get("period")
        if isinstance(bill_period, str) and bill_period.strip():
            plan_type = bill.get("plan_type")
            scope_label = (
                str(plan_type).strip()
                if isinstance(plan_type, str) and plan_type.strip()
                else None
            )
            return PresentationMeta(
                period_label=bill_period.strip(),
                scope_label=scope_label,
            )

    return None


def _finalize_chat_response(
    *,
    truth_result: TruthResult,
    options: list[ChatOption],
    message: str,
    source: str | None,
    presentation: ChatPresentation | None,
    backend_output: str,
) -> ChatResponse:
    if (
        truth_result.status == TruthStatus.AMBIGUOUS
        and options
    ):
        presentation = ChoiceListPresentation(
            title="Choose an option",
            prompt=(message or backend_output).strip()
            or None,
            choices=options,
        )

    presentation_meta = None
    if truth_result.status == TruthStatus.VERIFIED:
        presentation_meta = _presentation_meta_from_truth(
            truth_result,
        )

    return ChatResponse(
        message=message,
        status=truth_result.status.value,
        source=source,
        presentation=presentation,
        presentation_meta=presentation_meta,
        options=options,
    )


def _result_type_from_truth(
    truth_result: TruthResult,
) -> str | None:
    data = truth_result.data

    if not isinstance(data, dict):
        return None

    result_type = data.get("result_type")

    return result_type if isinstance(result_type, str) else None


class ChatService:
    """Coordinate intent extraction, truth retrieval and presentation."""

    def __init__(
        self,
        llm_client: GroqLLMClient,
        conversation_service: ConversationService | None = None,
        chat_history_service: ChatHistoryService | None = None,
    ) -> None:
        self._llm_client = llm_client
        self._conversation_service = (
            conversation_service
            or _DEFAULT_CONVERSATION_SERVICE
        )
        self._chat_history_service = (
            chat_history_service
            or _DEFAULT_CHAT_HISTORY_SERVICE
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

        (
            truth_result,
            options,
            intent_name,
            resolved_conversation_id,
        ) = self._process_turn(
            db=db,
            customer=customer,
            user_message=user_message,
            conversation_id=conversation_id,
        )

        response = self._build_chat_response(
            truth_result=truth_result,
            options=options,
            intent_name=intent_name,
        )
        self._persist_history(
            db=db,
            customer=customer,
            conversation_id=resolved_conversation_id,
            user_message=user_message,
            response=response,
        )
        return response

    def respond_stream(
        self,
        *,
        db: sqlite3.Connection,
        customer: CustomerContext,
        user_message: str,
        conversation_id: str | None = None,
    ) -> tuple[ChatResponse, Iterator[str]]:
        """Resolve a turn on the backend and stream only its final wording."""

        (
            truth_result,
            options,
            intent_name,
            resolved_conversation_id,
        ) = self._process_turn(
            db=db,
            customer=customer,
            user_message=user_message,
            conversation_id=conversation_id,
        )
        self._stream_conversation_id = resolved_conversation_id
        self._stream_user_message = user_message
        self._stream_customer = customer
        backend_output, presentation, skip_rewrite = (
            self._prepare_narrative(
                truth_result=truth_result,
                intent_name=intent_name,
            )
        )
        result_type = _result_type_from_truth(
            truth_result,
        )
        widget_only = result_type == "CUSTOMER_360"

        if widget_only:
            skip_rewrite = True
            backend_output = ""

        source = None
        if truth_result.source is not None:
            source = truth_result.source.source_name

        if skip_rewrite or widget_only:
            narrative_message = ""
            if not widget_only and presentation is None:
                narrative_message = backend_output
            elif (
                not widget_only
                and presentation is not None
                and backend_output.strip()
            ):
                # Widget-first turn: still expose narrative in metadata so
                # the client can unlock the composer without waiting on LLM.
                narrative_message = backend_output
            metadata = _finalize_chat_response(
                truth_result=truth_result,
                options=options,
                message=narrative_message,
                source=source,
                presentation=presentation,
                backend_output=backend_output,
            )
            return metadata, iter(())

        metadata = _finalize_chat_response(
            truth_result=truth_result,
            options=options,
            message="",
            source=source,
            presentation=presentation,
            backend_output=backend_output,
        )

        generate_response_stream = getattr(
            self._llm_client,
            "generate_response_stream",
            None,
        )
        result_type = _result_type_from_truth(
            truth_result,
        )
        profile = _narrative_profile(result_type)

        if callable(generate_response_stream):
            token_cap = rewrite_max_tokens(
                get_settings(),
                has_presentation=presentation is not None,
                result_type=result_type,
            )
            text_stream = generate_response_stream(
                backend_output,
                max_tokens=token_cap,
                narrative_profile=profile,
            )

            def stream_with_backend_fallback() -> Iterator[str]:
                received_text = False
                try:
                    for delta in text_stream:
                        if not delta:
                            continue
                        received_text = True
                        yield delta
                except LLMError:
                    if received_text:
                        raise
                    if backend_output:
                        yield backend_output
                    return
                if not received_text and backend_output:
                    yield backend_output

            return metadata, stream_with_backend_fallback()

        generate_response = getattr(
            self._llm_client,
            "generate_response",
            None,
        )
        try:
            token_cap = rewrite_max_tokens(
                get_settings(),
                has_presentation=presentation is not None,
                result_type=result_type,
            )
            final_message = (
                generate_response(
                    backend_output,
                    max_tokens=token_cap,
                    narrative_profile=profile,
                )
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
    ) -> tuple[
        TruthResult,
        list[ChatOption],
        str | None,
        str,
    ]:
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
            context_hint=context.build_intent_context(),
        )
        context.update(intent_response, truth_result)
        context.record_turn(
            user_message,
            intent_response,
            truth_result,
        )
        options = [
            ChatOption(
                label=option.label,
                message=option.message,
            )
            for option in intent_response.options
        ]
        intent_name = intent_response.intent.value
        save_conversation_context(
            db,
            conversation_id=conversation_id,
            customer_id=customer.customer_id,
            context=context,
        )
        return (
            truth_result,
            options,
            intent_name,
            conversation_id,
        )

    def persist_streamed_response(
        self,
        db: sqlite3.Connection,
        *,
        response: ChatResponse,
        assistant_message: str,
    ) -> None:
        conversation_id = getattr(
            self,
            "_stream_conversation_id",
            None,
        )
        user_message = getattr(
            self,
            "_stream_user_message",
            None,
        )
        customer = getattr(self, "_stream_customer", None)

        if (
            not conversation_id
            or not user_message
            or customer is None
        ):
            return

        merged = ChatResponse(
            message=assistant_message or response.message,
            status=response.status,
            source=response.source,
            presentation=response.presentation,
            presentation_meta=response.presentation_meta,
            options=response.options,
        )
        self._persist_history(
            db=db,
            customer=customer,
            conversation_id=conversation_id,
            user_message=user_message,
            response=merged,
        )

    def _persist_history(
        self,
        *,
        db: sqlite3.Connection,
        customer: CustomerContext,
        conversation_id: str,
        user_message: str,
        response: ChatResponse,
    ) -> None:
        assistant_text = response.message.strip()
        if not assistant_text and response.presentation is None:
            return

        self._chat_history_service.record_exchange(
            db,
            conversation_id=conversation_id,
            customer_id=customer.customer_id,
            user_message=user_message,
            assistant_message=assistant_text,
            status=response.status,
            source=response.source,
            presentation=response.presentation,
            presentation_meta=response.presentation_meta,
            options=response.options,
        )

    def _prepare_narrative(
        self,
        *,
        truth_result: TruthResult,
        intent_name: str | None,
    ) -> tuple[str, ChatPresentation | None, bool]:
        backend_output = (
            self._response_service.build_response(
                truth_result,
            )
        )
        presentation = (
            self._presentation_service.build(
                truth_result,
            )
        )
        settings = get_settings()
        result_type = _result_type_from_truth(
            truth_result,
        )
        skip_rewrite = should_skip_response_rewrite(
            truth_result.status,
            presentation,
            settings.response_llm_mode,
            result_type=result_type,
        )
        presentation_type = (
            presentation.type
            if presentation is not None
            else None
        )

        log_response_turn(
            intent=intent_name,
            status=truth_result.status.value,
            result_type=_result_type_from_truth(
                truth_result,
            ),
            backend_output_chars=len(
                backend_output,
            ),
            presentation_type=presentation_type,
            rewrite_skipped=skip_rewrite,
            response_llm_mode=settings.response_llm_mode,
        )

        return backend_output, presentation, skip_rewrite

    def _build_chat_response(
        self,
        *,
        truth_result: TruthResult,
        options: list[ChatOption],
        intent_name: str | None = None,
        message_override: str | None = None,
        presentation: ChatPresentation | None = None,
        skip_rewrite: bool | None = None,
        backend_output: str | None = None,
    ) -> ChatResponse:
        if backend_output is None or presentation is None or skip_rewrite is None:
            backend_output, presentation, skip_rewrite = (
                self._prepare_narrative(
                    truth_result=truth_result,
                    intent_name=intent_name,
                )
            )

        generate_response = getattr(
            self._llm_client,
            "generate_response",
            None,
        )
        message = message_override

        if message is None:
            if skip_rewrite:
                message = backend_output
            else:
                try:
                    result_type = _result_type_from_truth(
                        truth_result,
                    )
                    profile = _narrative_profile(
                        result_type,
                    )
                    token_cap = rewrite_max_tokens(
                        get_settings(),
                        has_presentation=presentation is not None,
                        result_type=result_type,
                    )
                    message = (
                        generate_response(
                            backend_output,
                            max_tokens=token_cap,
                            narrative_profile=profile,
                        )
                        if callable(generate_response)
                        else backend_output
                    )
                except LLMError:
                    message = backend_output

        if not (message or "").strip():
            message = backend_output

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

        return _finalize_chat_response(
            truth_result=truth_result,
            options=options,
            message=message,
            source=source,
            presentation=presentation,
            backend_output=backend_output,
        )
