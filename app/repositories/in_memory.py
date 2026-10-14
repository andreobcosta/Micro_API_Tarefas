"""Repositório de tarefas em memória, usado nos testes unitários."""

import uuid
from dataclasses import replace

from app.models.task import Task, TaskStatus


class InMemoryTaskRepository:
    """Implementação de `TaskRepository` que guarda as tarefas em um dicionário.

    Guarda e devolve cópias das tarefas, para que alterações feitas pelo
    chamador no objeto não mudem o que está armazenado.
    """

    def __init__(self) -> None:
        self._tasks: dict[uuid.UUID, Task] = {}

    def add(self, task: Task) -> Task:
        """Grava uma cópia da tarefa e devolve outra cópia."""
        self._tasks[task.id] = replace(task)
        return replace(task)

    def get(self, task_id: uuid.UUID) -> Task | None:
        """Devolve uma cópia da tarefa, ou `None` se não existir."""
        task = self._tasks.get(task_id)
        return replace(task) if task is not None else None

    def list(
        self, status: TaskStatus | None, limit: int, offset: int
    ) -> tuple[list[Task], int]:
        """Lista cópias por `created_at` e `id` decrescentes, com filtro e paginação."""
        matching = [t for t in self._tasks.values() if status in (None, t.status)]
        matching.sort(key=lambda t: (t.created_at, t.id), reverse=True)
        page = matching[offset : offset + limit]
        return [replace(t) for t in page], len(matching)

    def update(self, task: Task) -> bool:
        """Substitui a tarefa de mesmo id; `False` se ela não existir."""
        if task.id not in self._tasks:
            return False
        self._tasks[task.id] = replace(task)
        return True

    def delete(self, task_id: uuid.UUID) -> bool:
        """Remove a tarefa; `False` se ela não existir."""
        return self._tasks.pop(task_id, None) is not None
