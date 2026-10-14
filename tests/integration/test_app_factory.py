"""Testes da montagem da aplicação: injeção de repositório e padrão SQL."""

from fastapi.testclient import TestClient

from app.main import create_app
from app.repositories.in_memory import InMemoryTaskRepository
from app.repositories.sql_repository import SqlTaskRepository


def test_injected_repository_is_used() -> None:
    repository = InMemoryTaskRepository()

    app = create_app(repository=repository)

    assert app.state.task_repository is repository


def test_sql_repository_is_the_default() -> None:
    app = create_app()

    assert isinstance(app.state.task_repository, SqlTaskRepository)


def test_default_app_creates_tables_on_startup() -> None:
    app = create_app()

    with TestClient(app) as client:
        created = client.post("/tarefas", json={"titulo": "Persistir de verdade"})
        listed = client.get("/tarefas")

    assert created.status_code == 201
    assert listed.json()["total"] == 1
