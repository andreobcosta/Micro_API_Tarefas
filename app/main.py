"""Criação da aplicação FastAPI."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Engine

from app.api import health, tasks
from app.api.error_handlers import register_error_handlers
from app.api.openapi import install_portuguese_openapi
from app.core import messages
from app.core.config import Settings
from app.db.session import create_db_engine, create_session_factory, create_tables
from app.repositories.base import TaskRepository
from app.repositories.sql_repository import SqlTaskRepository

# Interface web estática (HTML, CSS e JavaScript puros), servida pela própria API.
STATIC_DIR = Path(__file__).parent / "static"
WEB_MOUNT_PATH = "/app"


def create_app(
    repository: TaskRepository | None = None, settings: Settings | None = None
) -> FastAPI:
    """Cria uma aplicação nova, com o seu próprio repositório.

    Args:
        repository: Repositório injetado (usado nos testes). Quando omitido,
            usa o repositório SQL configurado por `DATABASE_URL`.
        settings: Configuração; lida do ambiente quando omitida.

    O engine é criado sem abrir conexão; as tabelas são criadas na partida
    (lifespan), então importar este módulo não toca o disco.
    """
    engine: Engine | None = None
    if repository is None:
        url = (settings or Settings.from_env()).database_url
        engine = create_db_engine(url)
        repository = SqlTaskRepository(create_session_factory(engine))

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if engine is not None:
            create_tables(engine)
        yield
        if engine is not None:
            engine.dispose()

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
        lifespan=lifespan,
    )
    app.state.task_repository = repository
    app.include_router(health.router)
    app.include_router(tasks.router)
    app.mount(WEB_MOUNT_PATH, StaticFiles(directory=STATIC_DIR, html=True), name="web")
    register_error_handlers(app)
    install_portuguese_openapi(app)
    return app


app = create_app()
