"""Structured-data orchestration service for NexaTel."""

from __future__ import annotations

import sqlite3

from app.intent.parameters import normalize_parameters
from app.intent.router import IntentRouter
from app.llm.extractor import IntentExtractor
from app.models.domain import CustomerContext
from app.models.llm import LLMIntentResponse
from app.truth.result import TruthResult, ambiguous_result


class StructuredDataService:
    """Execute supported structured-data customer requests."""

    def __init__(
        self,
        intent_extractor: IntentExtractor,
        intent_router: IntentRouter,
    ) -> None:
        self._intent_extractor = intent_extractor
        self._intent_router = intent_router

    def execute(
        self,
        db: sqlite3.Connection,
        customer: CustomerContext,
        user_message: str,
    ) -> tuple[LLMIntentResponse, TruthResult]:
        """Extract an intent and execute its backend handler.

        Returns:
            The structured LLM intent response and the verified backend
            TruthResult.
        """

        llm_intent = self._intent_extractor.extract(
            user_message
        )

        if llm_intent.clarification:
            return llm_intent, ambiguous_result(
                message=llm_intent.clarification,
            )

        parameters = normalize_parameters(
            llm_intent.parameters
        )

        result = self._intent_router.route(
            db=db,
            customer=customer,
            intent=llm_intent.intent,
            parameters=parameters,
        )

        return llm_intent, result