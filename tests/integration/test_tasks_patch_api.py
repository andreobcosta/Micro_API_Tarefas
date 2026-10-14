"""Testes da rota `PATCH /tarefas/{id}` (RF05)."""

import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from fastapi.testclient import TestClient

CreateTask = Callable[..., dict[str, Any]]


def _instant(value: str) -> datetime:
    return datetime.fromisoformat(value)


class TestPatch:
    def test_changes_only_the_sent_field(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        task = create_task(
            "Título original", descricao="Descrição", status="em_andamento"
        )

        response = client.patch(
            f"/tarefas/{task['id']}", json={"titulo": "Novo título"}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["titulo"] == "Novo título"
        assert body["descricao"] == "Descrição"
        assert body["status"] == "em_andamento"
        assert body["id"] == task["id"]
        assert body["criado_em"] == task["criado_em"]

    def test_changes_only_status(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        task = create_task("Título original", descricao="Descrição")

        response = client.patch(f"/tarefas/{task['id']}", json={"status": "concluida"})

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "concluida"
        assert body["titulo"] == "Título original"
        assert body["descricao"] == "Descrição"

    def test_null_description_clears_it(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        task = create_task("Título original", descricao="Descrição")

        response = client.patch(f"/tarefas/{task['id']}", json={"descricao": None})

        assert response.status_code == 200
        body = response.json()
        assert body["descricao"] is None
        assert body["titulo"] == "Título original"

    def test_title_is_trimmed(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        task = create_task()

        response = client.patch(f"/tarefas/{task['id']}", json={"titulo": "  Novo  "})

        assert response.json()["titulo"] == "Novo"

    def test_updates_updated_at_only(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        task = create_task()

        body = client.patch(
            f"/tarefas/{task['id']}", json={"status": "concluida"}
        ).json()

        assert body["criado_em"] == task["criado_em"]
        assert _instant(body["atualizado_em"]) > _instant(task["atualizado_em"])

    def test_change_is_persisted(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        task = create_task()
        client.patch(f"/tarefas/{task['id']}", json={"status": "concluida"})

        assert client.get(f"/tarefas/{task['id']}").json()["status"] == "concluida"

    def test_unknown_task_returns_404(self, client: TestClient) -> None:
        response = client.patch(
            f"/tarefas/{uuid.uuid4()}", json={"status": "concluida"}
        )

        assert response.status_code == 404
        assert response.json() == {
            "codigo": "TAREFA_NAO_ENCONTRADA",
            "mensagem": "Tarefa não encontrada.",
            "detalhes": [],
        }


class TestPatchValidation:
    def test_empty_body_is_rejected_with_message_in_details(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        task = create_task()

        response = client.patch(f"/tarefas/{task['id']}", json={})

        assert response.status_code == 422
        assert response.json() == {
            "codigo": "VALIDACAO_INVALIDA",
            "mensagem": "Os dados enviados são inválidos.",
            "detalhes": [
                {
                    "campo": "corpo",
                    "mensagem": "Informe ao menos um campo para atualizar.",
                }
            ],
        }

    def test_null_title_is_rejected(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        task = create_task()

        response = client.patch(f"/tarefas/{task['id']}", json={"titulo": None})

        assert response.status_code == 422
        assert response.json()["detalhes"][0]["campo"] == "titulo"

    def test_null_status_is_rejected(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        task = create_task()

        response = client.patch(f"/tarefas/{task['id']}", json={"status": None})

        assert response.status_code == 422
        assert response.json()["detalhes"][0]["campo"] == "status"

    def test_short_title_is_rejected(
        self, client: TestClient, create_task: CreateTask
    ) -> None:
        task = create_task()

        response = client.patch(f"/tarefas/{task['id']}", json={"titulo": "x"})

        assert response.status_code == 422
        assert response.json()["detalhes"] == [
            {"campo": "titulo", "mensagem": "Deve ter no mínimo 3 caracteres."}
        ]

    def test_invalid_task_id_is_rejected(self, client: TestClient) -> None:
        response = client.patch("/tarefas/abc", json={"status": "concluida"})

        assert response.status_code == 422
        assert response.json()["detalhes"][0]["campo"] == "id"
