"""Dependências injetadas nas rotas (`Depends`)."""

from fastapi import Request

from app.services.task_service import TaskService


def get_task_service(request: Request) -> TaskService:
    """Entrega o `TaskService` ligado ao repositório da aplicação.

    O repositório fica em `app.state.task_repository`, criado em `create_app()`;
    assim cada aplicação (e cada teste) tem o seu, e os testes podem trocar o
    serviço por `app.dependency_overrides[get_task_service]`.
    """
    return TaskService(request.app.state.task_repository)
