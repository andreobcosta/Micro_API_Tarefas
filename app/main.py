"""Criação da aplicação FastAPI."""

from fastapi import FastAPI

from app.api import health, tasks
from app.api.error_handlers import register_error_handlers
from app.core import messages
from app.repositories.in_memory import InMemoryTaskRepository


def create_app() -> FastAPI:
    """Cria uma aplicação nova, com o seu próprio repositório em memória.

    Cada chamada devolve uma aplicação independente (usado para isolar testes).
    """
    app = FastAPI(
        title=messages.APP_TITLE,
        description=messages.APP_DESCRIPTION,
        version=messages.APP_VERSION,
        openapi_tags=[
            {"name": messages.TAG_TASKS, "description": messages.TAG_TASKS_DESCRIPTION},
            {
                "name": messages.TAG_HEALTH,
                "description": messages.TAG_HEALTH_DESCRIPTION,
            },
        ],
        docs_url="/documentacao",
        redoc_url="/referencia",
        openapi_url="/esquema-openapi.json",
    )
    app.state.task_repository = InMemoryTaskRepository()
    app.include_router(health.router)
    app.include_router(tasks.router)
    register_error_handlers(app)
    return app


app = create_app()
