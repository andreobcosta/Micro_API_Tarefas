"""Fixtures da camada HTTP: uma aplicação (e um repositório) novos por teste."""

from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Cliente com lifespan ativo (cria as tabelas do SQLite em memória)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def create_task(client: TestClient) -> Callable[..., dict[str, Any]]:
    """Cria uma tarefa via API e devolve o corpo da resposta."""

    def _create(titulo: str = "Estudar pytest", **extra: Any) -> dict[str, Any]:
        response = client.post("/tarefas", json={"titulo": titulo, **extra})
        assert response.status_code == 201, response.text
        return response.json()

    return _create
