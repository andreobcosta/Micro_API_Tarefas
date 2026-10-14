"""Handlers de exceção que traduzem erros para o contrato em português."""

import logging
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core import messages
from app.core.errors import TaskNotFoundError
from app.models.task import TaskStatus

logger = logging.getLogger(__name__)

_LOCATION_PREFIXES = {"body", "query", "path", "header", "cookie"}
_HTTP_ERRORS = {
    status.HTTP_404_NOT_FOUND: (
        messages.CODE_ROUTE_NOT_FOUND,
        messages.ROUTE_NOT_FOUND,
    ),
    status.HTTP_405_METHOD_NOT_ALLOWED: (
        messages.CODE_METHOD_NOT_ALLOWED,
        messages.METHOD_NOT_ALLOWED,
    ),
}


def error_body(
    code: str, message: str, details: list[dict[str, str]] | None = None
) -> dict[str, Any]:
    """Monta o corpo do contrato de erro `{codigo, mensagem, detalhes}`."""
    return {"codigo": code, "mensagem": message, "detalhes": details or []}


def _field_name(location: tuple[Any, ...]) -> str:
    """Converte o `loc` do Pydantic no nome do campo do contrato.

    Remove o prefixo de origem (`body`, `query`, `path`...) e usa `corpo` quando
    o erro é do corpo inteiro (por exemplo, JSON malformado).
    """
    parts = list(location)
    if parts and parts[0] in _LOCATION_PREFIXES:
        parts = parts[1:]
    if not any(isinstance(part, str) for part in parts):
        return messages.FIELD_BODY
    return ".".join(messages.FIELD_LABELS.get(str(part), str(part)) for part in parts)


def _message(error: Mapping[str, Any]) -> str:
    """Escolhe a mensagem em português para o tipo de erro do Pydantic."""
    error_type = error.get("type")
    context = error.get("ctx") or {}
    if error_type == "value_error":
        cause = str(context.get("error") or "")
        return cause or messages.VALIDATION_FALLBACK
    if error_type == "enum":
        values = ", ".join(item.value for item in TaskStatus)
        return messages.VALIDATION_ENUM.format(values=values)
    template = messages.VALIDATION_MESSAGES.get(str(error_type))
    if template is None:
        return messages.VALIDATION_FALLBACK
    try:
        return template.format_map(context)
    except (KeyError, IndexError):
        return messages.VALIDATION_FALLBACK


def translate_validation_error(error: Mapping[str, Any]) -> dict[str, str]:
    """Traduz um erro do Pydantic para `{campo, mensagem}`, sem vazar `input`/`ctx`."""
    return {
        "campo": _field_name(tuple(error.get("loc", ()))),
        "mensagem": _message(error),
    }


def handle_task_not_found(_: Request, exc: Exception) -> JSONResponse:
    """Converte `TaskNotFoundError` em 404 `TAREFA_NAO_ENCONTRADA`."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_body(messages.CODE_TASK_NOT_FOUND, str(exc)),
    )


def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Converte `RequestValidationError` em 422 `VALIDACAO_INVALIDA`."""
    details = [translate_validation_error(error) for error in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=error_body(
            messages.CODE_VALIDATION, messages.VALIDATION_FAILED, details
        ),
    )


def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Converte erros HTTP do framework (404/405 de rota e outros) em português."""
    code, message = _HTTP_ERRORS.get(
        exc.status_code, (messages.CODE_HTTP_ERROR, messages.HTTP_ERROR)
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(code, message),
        headers=exc.headers,
    )


def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Converte qualquer exceção não tratada em 500 `ERRO_INTERNO` genérico.

    O detalhe da exceção vai só para o log do servidor, nunca para o cliente.
    """
    logger.error(
        messages.LOG_UNHANDLED_ERROR, request.method, request.url.path, exc_info=exc
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_body(messages.CODE_INTERNAL_ERROR, messages.INTERNAL_ERROR),
    )


def register_error_handlers(app: FastAPI) -> None:
    """Registra os handlers de erro na aplicação."""
    app.add_exception_handler(TaskNotFoundError, handle_task_not_found)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
