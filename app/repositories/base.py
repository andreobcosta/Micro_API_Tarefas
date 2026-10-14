"""Contrato de persistência de tarefas, independente de tecnologia."""

import uuid
from typing import Protocol

from app.models.task import Task, TaskStatus


class TaskRepository(Protocol):
    """Contrato que toda implementação de repositório de tarefas deve cumprir.

    O repositório só persiste e consulta; as regras de negócio (inclusive
    lançar erro para tarefa inexistente) ficam em `TaskService`.
    """

    def add(self, task: Task) -> Task:
        """Grava uma nova tarefa e a devolve."""
        ...

    def get(self, task_id: uuid.UUID) -> Task | None:
        """Busca uma tarefa pelo id; devolve `None` se não existir."""
        ...

    def list(
        self, status: TaskStatus | None, limit: int, offset: int
    ) -> tuple[list[Task], int]:
        """Lista tarefas por `created_at` decrescente, com paginação.

        Args:
            status: Filtro opcional por status.
            limit: Máximo de itens da página.
            offset: Quantidade de itens a pular.

        Returns:
            Tupla `(itens da página, total de tarefas que atendem ao filtro)`.
        """
        ...

    def update(self, task: Task) -> bool:
        """Substitui a tarefa de mesmo id; devolve `False` se ela não existir."""
        ...

    def delete(self, task_id: uuid.UUID) -> bool:
        """Remove a tarefa; devolve `False` se ela não existir."""
        ...
