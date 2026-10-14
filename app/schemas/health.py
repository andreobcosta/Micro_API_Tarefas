"""Esquema da verificação de saúde."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Corpo de `GET /saude`."""

    status: str
