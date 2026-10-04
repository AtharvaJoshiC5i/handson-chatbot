"""Structured logging for chat turn LLM and narrative usage."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def log_intent_llm_usage(
    *,
    intent: str | None,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    total_tokens: int | None,
    deterministic: bool = False,
) -> None:
    logger.info(
        "chat_intent_llm",
        extra={
            "intent": intent,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "deterministic": deterministic,
        },
    )


def log_response_turn(
    *,
    intent: str | None,
    status: str,
    result_type: str | None,
    backend_output_chars: int,
    presentation_type: str | None,
    rewrite_skipped: bool,
    response_llm_mode: str,
) -> None:
    logger.info(
        "chat_response_turn",
        extra={
            "intent": intent,
            "status": status,
            "result_type": result_type,
            "backend_output_chars": backend_output_chars,
            "presentation_type": presentation_type,
            "rewrite_skipped": rewrite_skipped,
            "response_llm_mode": response_llm_mode,
        },
    )


def log_response_rewrite_usage(
    *,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    total_tokens: int | None,
    max_tokens: int,
    streamed: bool,
) -> None:
    logger.info(
        "chat_response_rewrite_llm",
        extra={
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "max_tokens": max_tokens,
            "streamed": streamed,
        },
    )


def extract_usage_tokens(
    response: Any,
) -> tuple[int | None, int | None, int | None]:
    usage = getattr(response, "usage", None)

    if usage is None:
        return None, None, None

    prompt = getattr(usage, "prompt_tokens", None)
    completion = getattr(usage, "completion_tokens", None)
    total = getattr(usage, "total_tokens", None)

    return prompt, completion, total
