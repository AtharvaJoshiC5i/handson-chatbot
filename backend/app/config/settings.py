"""Application configuration for NexaTel."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = BACKEND_ROOT / "data" / "nexatel.db"


class Settings(BaseSettings):
    """NexaTel application settings."""

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = Field(
        default="development",
        alias="ENVIRONMENT",
    )

    database_path: str = Field(
        default=str(DEFAULT_DATABASE_PATH),
        alias="DATABASE_PATH",
    )

    groq_api_key: str = Field(
        default="",
        alias="GROQ_API_KEY",
    )

    groq_model: str = Field(
        default="openai/gpt-oss-20b",
        alias="GROQ_MODEL",
    )

    llm_timeout_seconds: float = Field(
        default=30.0,
        alias="LLM_TIMEOUT_SECONDS",
    )

    response_llm_mode: str = Field(
        default="auto",
        alias="RESPONSE_LLM_MODE",
        description=(
            "auto|light: skip Groq rewrite when structured "
            "presentation exists; off: never rewrite; full: always rewrite"
        ),
    )

    response_max_tokens_light: int = Field(
        default=192,
        alias="RESPONSE_MAX_TOKENS",
        ge=32,
        le=768,
    )

    response_max_tokens_full: int = Field(
        default=640,
        alias="RESPONSE_MAX_TOKENS_FULL",
        ge=64,
        le=768,
    )

    conversation_turn_window: int = Field(
        default=10,
        alias="CONVERSATION_TURN_WINDOW",
        ge=1,
        le=50,
        description=(
            "Max prior user turns kept per conversation_id for intent context"
        ),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()