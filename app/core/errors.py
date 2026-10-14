"""Exceções de domínio."""

from app.core import messages


class TaskNotFoundError(Exception):
    """A tarefa solicitada não existe."""

    def __init__(self, message: str = messages.TASK_NOT_FOUND) -> None:
        super().__init__(message)
