"""Regras de negócio das tarefas."""

import uuid
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone

from app.core.errors import TaskNotFoundError
from app.models.task import Task, TaskStatus
from app.repositories.base import TaskRepository
from app.schemas.task import TaskCreate, TaskReplace, TaskUpdate

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    """Relógio padrão: instante atual em UTC, com timezone."""
    return datetime.now(timezone.utc)


class TaskService:
    """Casos de uso de tarefas; depende apenas do contrato `TaskRepository`."""

    def __init__(self, repository: TaskRepository, clock: Clock = utc_now) -> None:
        """Cria o serviço.

        Args:
            repository: Repositório de tarefas (qualquer implementação do Protocol).
            clock: Função que devolve o instante atual em UTC; injetável nos testes.
        """
        self._repository = repository
        self._clock = clock

    def create(self, data: TaskCreate) -> Task:
        """Cria uma tarefa com id novo e `created_at` igual a `updated_at`."""
        now = self._clock()
        task = Task(
            id=uuid.uuid4(),
            title=data.title,
            description=data.description,
            status=data.status,
            created_at=now,
            updated_at=now,
        )
        return self._repository.add(task)

    def list(
        self, status: TaskStatus | None, limit: int, offset: int
    ) -> tuple[list[Task], int]:
        """Lista tarefas (mais recentes primeiro) e o total do filtro."""
        return self._repository.list(status, limit, offset)

    def get(self, task_id: uuid.UUID) -> Task:
        """Busca uma tarefa.

        Raises:
            TaskNotFoundError: Se o id não existir.
        """
        task = self._repository.get(task_id)
        if task is None:
            raise TaskNotFoundError()
        return task

    def replace(self, task_id: uuid.UUID, data: TaskReplace) -> Task:
        """Substitui título, descrição e status (PUT); descrição ausente vira `None`.

        Raises:
            TaskNotFoundError: Se o id não existir.
        """
        current = self.get(task_id)
        return self._save(
            replace(
                current,
                title=data.title,
                description=data.description,
                status=data.status,
            )
        )

    def update(self, task_id: uuid.UUID, data: TaskUpdate) -> Task:
        """Altera só os campos enviados (PATCH); `descricao=None` limpa a descrição.

        Raises:
            TaskNotFoundError: Se o id não existir.
        """
        current = self.get(task_id)
        changes = {name: getattr(data, name) for name in data.model_fields_set}
        return self._save(replace(current, **changes))

    def delete(self, task_id: uuid.UUID) -> None:
        """Remove uma tarefa.

        Raises:
            TaskNotFoundError: Se o id não existir.
        """
        if not self._repository.delete(task_id):
            raise TaskNotFoundError()

    def _save(self, task: Task) -> Task:
        """Atualiza `updated_at` e persiste a tarefa alterada."""
        task = replace(task, updated_at=self._clock())
        if not self._repository.update(task):
            raise TaskNotFoundError()
        return task
