"""Esquemas Pydantic do contrato público (campos em português via alias)."""

import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.core import messages
from app.models.task import TaskStatus

Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=3, max_length=100)
]
Description = Annotated[str, Field(max_length=500)]


class TaskCreate(BaseModel):
    """Corpo do `POST /tarefas`."""

    model_config = ConfigDict(populate_by_name=True)

    title: Title = Field(alias="titulo")
    description: Description | None = Field(default=None, alias="descricao")
    status: TaskStatus = TaskStatus.PENDING


class TaskReplace(BaseModel):
    """Corpo do `PUT /tarefas/{id}`: exige título e status."""

    model_config = ConfigDict(populate_by_name=True)

    title: Title = Field(alias="titulo")
    description: Description | None = Field(default=None, alias="descricao")
    status: TaskStatus


class TaskUpdate(BaseModel):
    """Corpo do `PATCH /tarefas/{id}`.

    Os campos ausentes não são alterados (use `model_fields_set` para saber o
    que foi enviado). `titulo` e `status` não aceitam `null`; `descricao`
    aceita `null` para limpar a descrição. O `None` padrão não é validado
    pelo Pydantic, por isso só vale para campos ausentes.
    """

    model_config = ConfigDict(populate_by_name=True)

    title: Title = Field(default=None, alias="titulo")  # type: ignore[assignment]
    description: Description | None = Field(default=None, alias="descricao")
    status: TaskStatus = Field(default=None)  # type: ignore[assignment]

    @model_validator(mode="after")
    def _require_at_least_one_field(self) -> Self:
        """Rejeita o corpo vazio."""
        if not self.model_fields_set:
            raise ValueError(messages.PATCH_EMPTY_BODY)
        return self


class TaskResponse(BaseModel):
    """Tarefa devolvida pela API; serialize com `by_alias=True`."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: uuid.UUID
    title: str = Field(alias="titulo")
    description: str | None = Field(alias="descricao")
    status: TaskStatus
    created_at: datetime = Field(alias="criado_em")
    updated_at: datetime = Field(alias="atualizado_em")


class TaskListResponse(BaseModel):
    """Página de tarefas devolvida por `GET /tarefas`; serialize com `by_alias=True`."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[TaskResponse] = Field(alias="itens")
    total: int
    limit: int = Field(alias="limite")
    offset: int = Field(alias="deslocamento")
