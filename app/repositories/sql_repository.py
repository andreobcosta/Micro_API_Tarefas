"""Repositório de tarefas sobre SQLAlchemy (SQLite)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.core import messages
from app.db.models import TaskModel
from app.models.task import Task, TaskStatus


def _to_entity(model: TaskModel) -> Task:
    """Converte a linha do banco na entidade de domínio."""
    return Task(
        id=model.id,
        title=model.title,
        description=model.description,
        status=TaskStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _require_timezone(task: Task) -> None:
    """Recusa datas ingênuas: o contrato do domínio é UTC com fuso."""
    if task.created_at.tzinfo is None or task.updated_at.tzinfo is None:
        raise ValueError(messages.NAIVE_DATETIME)


def _to_model(task: Task) -> TaskModel:
    """Converte a entidade em linha do banco (status gravado pelo valor)."""
    _require_timezone(task)
    return TaskModel(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status.value,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _copy_into(model: TaskModel, task: Task) -> None:
    """Copia os campos da entidade para a linha existente."""
    _require_timezone(task)
    model.title = task.title
    model.description = task.description
    model.status = task.status.value
    model.created_at = task.created_at
    model.updated_at = task.updated_at


class SqlTaskRepository:
    """Implementação de `TaskRepository` em banco SQL.

    Abre uma sessão curta por operação e faz `commit` ao fim de cada escrita.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, task: Task) -> Task:
        """Grava a tarefa e a devolve."""
        with self._session_factory() as session:
            session.add(_to_model(task))
            session.commit()
        return task

    def get(self, task_id: uuid.UUID) -> Task | None:
        """Busca por id; `None` se não existir."""
        with self._session_factory() as session:
            model = session.get(TaskModel, task_id)
            return _to_entity(model) if model is not None else None

    def list(
        self, status: TaskStatus | None, limit: int, offset: int
    ) -> tuple[list[Task], int]:
        """Lista por `created_at` e `id` decrescentes, com filtro e paginação."""
        filters = [] if status is None else [TaskModel.status == status.value]
        with self._session_factory() as session:
            total = session.scalar(
                select(func.count()).select_from(TaskModel).where(*filters)
            )
            rows = session.scalars(
                select(TaskModel)
                .where(*filters)
                .order_by(TaskModel.created_at.desc(), TaskModel.id.desc())
                .limit(limit)
                .offset(offset)
            ).all()
            return [_to_entity(row) for row in rows], total or 0

    def update(self, task: Task) -> bool:
        """Substitui a tarefa de mesmo id; `False` se não existir."""
        with self._session_factory() as session:
            model = session.get(TaskModel, task.id)
            if model is None:
                return False
            _copy_into(model, task)
            session.commit()
            return True

    def delete(self, task_id: uuid.UUID) -> bool:
        """Remove a tarefa; `False` se não existir."""
        with self._session_factory() as session:
            model = session.get(TaskModel, task_id)
            if model is None:
                return False
            session.delete(model)
            session.commit()
            return True
