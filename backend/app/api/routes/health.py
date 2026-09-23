from fastapi import APIRouter, Depends

from app.config.settings import Settings, get_settings
from app.models.api import HealthResponse


router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
)
def health_check(
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """
    Return basic application health information.

    Database and Azure OpenAI connectivity checks will be added
    later when those layers are implemented.
    """

    return HealthResponse(
        status="ok",
        environment=settings.environment,
    )