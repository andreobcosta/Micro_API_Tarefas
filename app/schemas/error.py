"""Esquemas do contrato de erro, usados na documentação OpenAPI."""

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    """Item de `detalhes`: o campo com problema e o que há de errado."""

    model_config = ConfigDict(populate_by_name=True)

    field: str = Field(alias="campo", description="Campo com problema.")
    message: str = Field(alias="mensagem", description="O que há de errado.")


class ErrorResponse(BaseModel):
    """Corpo de toda resposta de erro: `{codigo, mensagem, detalhes}`."""

    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(alias="codigo", description="Código estável do erro.")
    message: str = Field(alias="mensagem", description="Resumo legível do erro.")
    details: list[ErrorDetail] = Field(
        alias="detalhes", description="Problemas por campo; vazio quando não há."
    )
