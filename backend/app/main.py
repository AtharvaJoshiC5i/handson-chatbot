"""NexaTel FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.config.settings import get_settings


settings = get_settings()

app = FastAPI(
    title="NexaTel AI Customer Support",
    description=(
        "Phase 1 structured-data customer support API "
        "for NexaTel."
    ),
    version="0.1.0",
)

app.include_router(
    health_router,
)

app.include_router(
    chat_router,
)