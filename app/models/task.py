"""Entidade de domínio `Task` e o enum `TaskStatus`."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Situação de uma tarefa: `pendente`, `em_andamento` ou `concluida`."""

    # Os nomes dos membros são em inglês; os valores são os do contrato.
    PENDING = "pendente"
    IN_PROGRESS = "em_andamento"
    DONE = "concluida"


@dataclass
class Task:
    """Tarefa do domínio, independente de Pydantic e de banco de dados.

    Attributes:
        id: Identificador único (UUID v4).
        title: Título já normalizado (3 a 100 caracteres).
        description: Descrição opcional (até 500 caracteres).
        status: Situação atual da tarefa.
        created_at: Instante de criação, em UTC.
        updated_at: Instante da última alteração, em UTC.
    """

    id: uuid.UUID
    title: str
    description: str | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
