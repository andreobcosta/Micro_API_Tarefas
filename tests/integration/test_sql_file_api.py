"""Integração da API sobre SQLite em ARQUIVO (tmp_path)."""

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.session import create_db_engine, create_session_factory
from app.main import create_app
from app.repositories.sql_repository import SqlTaskRepository


@pytest.fixture
def db_file(tmp_path: Path) -> Path:
    return tmp_path / "integracao.db"


def make_app(db_file: Path) -> FastAPI:
    return create_app(settings=Settings(database_url=f"sqlite:///{db_file}"))


@pytest.fixture
def client(db_file: Path) -> Iterator[TestClient]:
    """Cliente com lifespan ativo; o engine é descartado ao sair do `with`."""
    with TestClient(make_app(db_file)) as test_client:
        yield test_client


def create(client: TestClient, title: str, **extra: Any) -> dict[str, Any]:
    response = client.post("/tarefas", json={"titulo": title, **extra})
    assert response.status_code == 201, response.text
    return response.json()


class TestCrudOnFile:
    def test_full_lifecycle(self, client: TestClient, db_file: Path) -> None:
        created = create(client, "Ciclo completo", descricao="inicial")
        task_url = f"/tarefas/{created['id']}"
        assert db_file.exists()

        assert client.get(task_url).json() == created

        replaced = client.put(
            task_url, json={"titulo": "Substituída", "status": "em_andamento"}
        )
        assert replaced.status_code == 200
        assert replaced.json()["titulo"] == "Substituída"
        assert replaced.json()["descricao"] is None

        patched = client.patch(task_url, json={"status": "concluida"})
        assert patched.status_code == 200
        assert patched.json()["status"] == "concluida"
        assert patched.json()["titulo"] == "Substituída"

        assert client.get(task_url).json() == patched.json()

        assert client.delete(task_url).status_code == 204
        assert client.get(task_url).status_code == 404

    def test_dates_come_back_in_utc(self, client: TestClient) -> None:
        created = create(client, "Datas em UTC")

        fetched = client.get(f"/tarefas/{created['id']}").json()

        assert fetched["criado_em"].endswith(("Z", "+00:00"))
        assert fetched["criado_em"] == created["criado_em"]


class TestFilterAndPagination:
    def test_status_filter_returns_only_matching_tasks(
        self, client: TestClient
    ) -> None:
        create(client, "Pendente um")
        create(client, "Em andamento", status="em_andamento")
        create(client, "Concluída um", status="concluida")
        create(client, "Concluída dois", status="concluida")

        body = client.get("/tarefas", params={"status": "concluida"}).json()

        assert body["total"] == 2
        assert {item["status"] for item in body["itens"]} == {"concluida"}

    def test_pages_of_25_tasks_do_not_overlap(self, client: TestClient) -> None:
        for number in range(25):
            create(client, f"Tarefa {number:02d}")

        pages = [
            client.get("/tarefas", params={"limite": 10, "deslocamento": offset}).json()
            for offset in (0, 10, 20)
        ]

        assert [len(page["itens"]) for page in pages] == [10, 10, 5]
        assert {page["total"] for page in pages} == {25}
        ids = [item["id"] for page in pages for item in page["itens"]]
        assert len(ids) == len(set(ids)) == 25

    def test_offset_beyond_total_returns_empty_page_with_total(
        self, client: TestClient
    ) -> None:
        for number in range(3):
            create(client, f"Tarefa {number}")

        body = client.get("/tarefas", params={"deslocamento": 50}).json()

        assert body["itens"] == []
        assert body["total"] == 3


class TestPersistenceBetweenInstances:
    def test_second_app_sees_what_the_first_wrote(self, db_file: Path) -> None:
        with TestClient(make_app(db_file)) as first:
            created = create(first, "Sobrevive ao reinício")
            first.patch(f"/tarefas/{created['id']}", json={"status": "concluida"})

        with TestClient(make_app(db_file)) as second:
            listed = second.get("/tarefas").json()
            fetched = second.get(f"/tarefas/{created['id']}").json()

        assert listed["total"] == 1
        assert fetched["id"] == created["id"]
        assert fetched["status"] == "concluida"
        assert fetched["criado_em"] == created["criado_em"]


# --- Falha do banco: nada de detalhe interno vai ao cliente ---

ERROR_KEYS = {"codigo", "mensagem", "detalhes"}
SECRET_SQL = "INSERT INTO tasks (id, title, created_at) VALUES (?, ?, ?)"


def _forbidden_terms(db_file: Path) -> list[str]:
    return [
        "tasks",
        "SELECT",
        "INSERT",
        "sqlite",
        "OperationalError",
        ".db",
        "created_at",
        str(db_file),
        str(db_file.parent),
    ]


def _assert_generic_500(response: Any, db_file: Path) -> None:
    assert response.status_code == 500
    body = response.json()
    assert set(body) == ERROR_KEYS
    assert body["codigo"] == "ERRO_INTERNO"
    assert body["detalhes"] == []
    for term in _forbidden_terms(db_file):
        assert term not in response.text, term


class _ExplodingRepository:
    """Repositório que falha como um banco real, com detalhes internos."""

    def _boom(self, *_: Any, **__: Any) -> Any:
        raise SQLAlchemyError(f"(sqlite3.OperationalError) {SECRET_SQL} tasks.db")

    add = get = list = update = delete = _boom


class TestDatabaseFailureDoesNotLeak:
    def test_real_missing_table_returns_generic_500(self, db_file: Path) -> None:
        engine: Engine = create_db_engine(f"sqlite:///{db_file}")
        repository = SqlTaskRepository(create_session_factory(engine))
        app = create_app(repository=repository)  # sem lifespan: tabela inexistente
        client = TestClient(app, raise_server_exceptions=False)
        try:
            for response in (
                client.get("/tarefas"),
                client.post("/tarefas", json={"titulo": "Vai falhar"}),
            ):
                _assert_generic_500(response, db_file)
        finally:
            engine.dispose()

    @pytest.mark.parametrize(
        "method, url, payload",
        [
            ("GET", "/tarefas", None),
            ("POST", "/tarefas", {"titulo": "Vai falhar"}),
            ("GET", "/tarefas/00000000-0000-4000-8000-000000000000", None),
            ("DELETE", "/tarefas/00000000-0000-4000-8000-000000000000", None),
        ],
    )
    def test_simulated_driver_error_returns_generic_500(
        self, db_file: Path, method: str, url: str, payload: Any
    ) -> None:
        app = create_app(repository=_ExplodingRepository())  # type: ignore[arg-type]
        client = TestClient(app, raise_server_exceptions=False)

        response = client.request(method, url, json=payload)

        _assert_generic_500(response, db_file)

    def test_failure_is_logged_in_portuguese_and_detail_stays_server_side(
        self, db_file: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        app = create_app(repository=_ExplodingRepository())  # type: ignore[arg-type]
        client = TestClient(app, raise_server_exceptions=False)

        with caplog.at_level(logging.ERROR):
            response = client.get("/tarefas")

        assert any(
            "Erro interno não tratado" in record.getMessage()
            for record in caplog.records
        )
        assert SECRET_SQL not in response.text
