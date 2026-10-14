"""Rota de verificação de saúde."""

from fastapi import APIRouter

from app.core import messages
from app.schemas.health import HealthResponse

router = APIRouter(tags=[messages.TAG_HEALTH])


@router.get(
    "/saude",
    response_model=HealthResponse,
    summary=messages.SUMMARY_HEALTH,
    description=messages.DESCRIPTION_HEALTH,
    response_description=messages.RESPONSE_HEALTH,
)
def check_health() -> HealthResponse:
    """Responde que a aplicação está operacional."""
    return HealthResponse(status=messages.HEALTH_OK)
