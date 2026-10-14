"""Testes de integração das rotas de tarefas (RF01 a RF04, RF06 e RF07)."""

import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_task_service
from app.main import create_app

CreateTask = Callable[..., dict[str, Any]]


class TestCreate:
    def test_creates_task_with_defaults(self, client: TestClient) -> None:
        response = client.post("/tarefas", json={"titulo": "Estudar pytest"})

        assert response.status_code == 201
        body = response.json()
        assert uuid.UUID(body["id"]).version == 4
        assert body["titulo"] == "Estudar pytest"
        assert body["descricao"] is None
        assert body["status"] == "pendente"
        assert datetime.fromisoformat(body["criado_em"]).tzinfo is not None
        assert body["atualizado_em"] == body["criado_em"]

    def test_response_uses_only_contract_keys(self, client: TestClient) -> None:
        body = client.post("/tarefas", json={"titulo": "Estudar"}).json()

        assert set(body) == {
            "id",
            "titulo",
            "descricao",
            "status",
            "criado_em",
            "atualizado_em",
        }

    def test_strips_title_whitespace(self, client: TestClient) -> None:
        body = client.post("/tarefas", json={"titulo": "   Estudar   "}).json()

        assert body["titulo"] == "Estudar"

    def test_accepts_full_payload(self, client: TestClient) -> None:
        response = client.post(
            "/tarefas",
            json={"titulo": "Estudar", "descricao": "Cap. 3", "status": "em_andamento"},
        )

        assert response.status_code == 201
        assert response.json()["descricao"] == "Cap. 3"
        assert response.json()["status"] == "em_andamento"

    def test_short_title_is_rejected(self, client: TestClient) -> None:
        assert client.post("/tarefas", json={"titulo": "ab"}).status_code == 422

    def test_missing_title_is_rejected(self, client: TestClient) -> None:
        assert client.post("/tarefas", json={}).status_code == 422

    def test_created_task_can_be_fetched(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        created = create_task()

        assert client.get(f"/tarefas/{created['id']}").json() == created

    def test_internal_english_names_are_still_accepted(
        self, client: TestClient
    ) -> None:
        """Documenta o comportamento de `populate_by_name=True` (mantido de propósito).

        O contrato público é em português, mas a entrada também aceita o nome
        interno em inglês. Registrado em "Limitações" do README.
        """
        response = client.post("/tarefas", json={"title": "Estudar"})

        assert response.status_code == 201
        assert response.json()["titulo"] == "Estudar"


class TestList:
    def test_empty_list(self, client: TestClient) -> None:
        response = client.get("/tarefas")

        assert response.status_code == 200
        assert response.json() == {
            "itens": [],
            "total": 0,
            "limite": 10,
            "deslocamento": 0,
        }

    def test_paginates_25_tasks(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        for index in range(25):
            create_task(f"Tarefa {index:02d}")

        response = client.get("/tarefas", params={"limite": 10, "deslocamento": 20})

        body = response.json()
        assert response.status_code == 200
        assert len(body["itens"]) == 5
        assert body["total"] == 25
        assert body["limite"] == 10
        assert body["deslocamento"] == 20

    def test_orders_by_created_at_descending(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        for title in ("Primeira", "Segunda", "Terceira"):
            create_task(title)

        items = client.get("/tarefas").json()["itens"]

        assert [i["titulo"] for i in items] == ["Terceira", "Segunda", "Primeira"]

    def test_filters_by_status_and_total_reflects_filter(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        create_task("Pendente um")
        create_task("Concluida um", status="concluida")
        create_task("Concluida dois", status="concluida")

        body = client.get("/tarefas", params={"status": "concluida"}).json()

        assert body["total"] == 2
        assert {i["status"] for i in body["itens"]} == {"concluida"}

    def test_echoes_requested_page_values(self, client: TestClient) -> None:
        body = client.get("/tarefas", params={"limite": 100, "deslocamento": 3}).json()

        assert body["limite"] == 100
        assert body["deslocamento"] == 3

    @pytest.mark.parametrize(
        "params",
        [
            {"limite": 0},
            {"limite": 101},
            {"deslocamento": -1},
            {"status": "invalido"},
            {"limite": "abc"},
        ],
    )
    def test_invalid_query_params_are_rejected(
        self, client: TestClient, params: dict[str, Any]
    ) -> None:
        assert client.get("/tarefas", params=params).status_code == 422

    def test_limit_boundaries_are_accepted(self, client: TestClient) -> None:
        assert client.get("/tarefas", params={"limite": 1}).status_code == 200
        assert client.get("/tarefas", params={"limite": 100}).status_code == 200


class TestGet:
    def test_returns_existing_task(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        created = create_task()

        response = client.get(f"/tarefas/{created['id']}")

        assert response.status_code == 200
        assert response.json()["titulo"] == "Estudar pytest"

    def test_unknown_id_returns_404_in_the_error_contract(
        self, client: TestClient
    ) -> None:
        response = client.get(f"/tarefas/{uuid.uuid4()}")

        assert response.status_code == 404
        assert response.json() == {
            "codigo": "TAREFA_NAO_ENCONTRADA",
            "mensagem": "Tarefa não encontrada.",
            "detalhes": [],
        }

    def test_non_uuid_id_is_rejected(self, client: TestClient) -> None:
        assert client.get("/tarefas/nao-e-uuid").status_code == 422


class TestReplace:
    def test_replaces_the_task_and_refreshes_updated_at(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        created = create_task(descricao="Antiga")

        response = client.put(
            f"/tarefas/{created['id']}",
            json={"titulo": "Novo título", "status": "concluida"},
        )

        body = response.json()
        assert response.status_code == 200
        assert body["titulo"] == "Novo título"
        assert body["status"] == "concluida"
        assert body["descricao"] is None
        assert body["id"] == created["id"]
        assert body["criado_em"] == created["criado_em"]
        assert body["atualizado_em"] > created["atualizado_em"]

    def test_missing_status_is_rejected(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        created = create_task()

        response = client.put(f"/tarefas/{created['id']}", json={"titulo": "Novo"})

        assert response.status_code == 422

    def test_unknown_id_returns_404(self, client: TestClient) -> None:
        response = client.put(
            f"/tarefas/{uuid.uuid4()}", json={"titulo": "Novo", "status": "pendente"}
        )

        assert response.status_code == 404
        assert response.json()["codigo"] == "TAREFA_NAO_ENCONTRADA"


class TestDelete:
    def test_deletes_and_then_get_returns_404(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        created = create_task()

        response = client.delete(f"/tarefas/{created['id']}")

        assert response.status_code == 204
        assert response.content == b""
        assert client.get(f"/tarefas/{created['id']}").status_code == 404

    def test_unknown_id_returns_404(self, client: TestClient) -> None:
        response = client.delete(f"/tarefas/{uuid.uuid4()}")

        assert response.status_code == 404
        assert response.json()["codigo"] == "TAREFA_NAO_ENCONTRADA"


class TestHealth:
    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/saude")

        assert response.status_code == 200
        assert response.json() == {"status": "operacional"}


class TestIsolationAndWiring:
    def test_each_app_has_its_own_repository(self) -> None:
        first, second = TestClient(create_app()), TestClient(create_app())

        first.post("/tarefas", json={"titulo": "Só na primeira"})

        assert first.get("/tarefas").json()["total"] == 1
        assert second.get("/tarefas").json()["total"] == 0

    def test_service_can_be_replaced_with_dependency_overrides(
        self, app: FastAPI, client: TestClient
    ) -> None:
        class FakeService:
            def list(self, status: Any, limit: int, offset: int) -> tuple[list, int]:
                return [], 42

        app.dependency_overrides[get_task_service] = lambda: FakeService()

        assert client.get("/tarefas").json()["total"] == 42


class TestDocumentationRoutes:
    @pytest.mark.parametrize(
        "path", ["/documentacao", "/referencia", "/esquema-openapi.json"]
    )
    def test_portuguese_documentation_routes_exist(
        self, client: TestClient, path: str
    ) -> None:
        assert client.get(path).status_code == 200

    @pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
    def test_default_english_documentation_routes_are_disabled(
        self, client: TestClient, path: str
    ) -> None:
        assert client.get(path).status_code == 404

    def test_openapi_metadata_is_in_portuguese(self, client: TestClient) -> None:
        schema = client.get("/esquema-openapi.json").json()

        assert "Micro-API de Tarefas" in schema["info"]["title"]
        assert {tag["name"] for tag in schema["tags"]} == {"Tarefas", "Saúde"}

    def test_openapi_exposes_contract_property_names(self, client: TestClient) -> None:
        schema = client.get("/esquema-openapi.json").json()
        properties = {
            name
            for component in schema["components"]["schemas"].values()
            for name in component.get("properties", {})
        }

        assert {"titulo", "descricao", "criado_em", "atualizado_em"} <= properties
        assert not {"title", "description", "created_at", "updated_at"} & properties

    def test_every_operation_has_a_portuguese_response_description(
        self, client: TestClient
    ) -> None:
        schema = client.get("/esquema-openapi.json").json()

        for path, methods in schema["paths"].items():
            for method, operation in methods.items():
                assert operation.get("summary"), (path, method)
                for code, response in operation["responses"].items():
                    assert response["description"] != "Successful Response", (
                        path,
                        method,
                        code,
                    )
