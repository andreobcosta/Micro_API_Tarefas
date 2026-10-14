"""Handlers de exceção que traduzem erros para o contrato em português."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core import messages
from app.core.errors import TaskNotFoundError


def error_body(
    code: str, message: str, details: list[dict[str, str]] | None = None
) -> dict[str, Any]:
    """Monta o corpo do contrato de erro `{codigo, mensagem, detalhes}`."""
    return {"codigo": code, "mensagem": message, "detalhes": details or []}


def handle_task_not_found(_: Request, exc: Exception) -> JSONResponse:
    """Converte `TaskNotFoundError` em 404 `TAREFA_NAO_ENCONTRADA`."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_body(messages.CODE_TASK_NOT_FOUND, str(exc)),
    )


def register_error_handlers(app: FastAPI) -> None:
    """Registra os handlers de erro na aplicação."""
    app.add_exception_handler(TaskNotFoundError, handle_task_not_found)
