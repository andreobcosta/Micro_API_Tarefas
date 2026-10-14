"""Teste de idioma (RNF13): erros e OpenAPI saem em português do Brasil."""

import json
import uuid
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response

ERROR_KEYS = {"codigo", "mensagem", "detalhes"}
DETAIL_KEYS = {"campo", "mensagem"}
KNOWN_CODES = {
    "VALIDACAO_INVALIDA",
    "TAREFA_NAO_ENCONTRADA",
    "ROTA_NAO_ENCONTRADA",
    "METODO_NAO_PERMITIDO",
    "ERRO_HTTP",
    "ERRO_INTERNO",
}
ENGLISH_MARKERS = [
    "field required",
    "input should",
    "string should",
    "value error",
    "not found",
    "method not allowed",
    "internal server error",
    "unprocessable",
    "validation error",
    "invalid",
    "successful response",
    "ensure this value",
    "missing",
    "forbidden",
]
OPENAPI_FORBIDDEN = [
    "Successful Response",
    "Validation Error",
    "HTTPValidationError",
    "ValidationError",
]


def _has_english_marker(text: str) -> str | None:
    lowered = text.lower()
    return next((m for m in ENGLISH_MARKERS if m in lowered), None)


def _error_responses(client: TestClient) -> list[tuple[str, Response]]:
    """Dispara um cenário de cada tipo de erro e devolve as respostas."""
    unknown = f"/tarefas/{uuid.uuid4()}"
    return [
        ("tarefa inexistente", client.get(unknown)),
        ("rota inexistente", client.get("/nao-existe")),
        ("método não permitido", client.put("/tarefas", json={})),
        ("corpo vazio", client.post("/tarefas", json={})),
        ("título curto", client.post("/tarefas", json={"titulo": "ab"})),
        (
            "status inválido",
            client.post("/tarefas", json={"titulo": "ok!", "status": "x"}),
        ),
        ("tipo errado", client.post("/tarefas", json={"titulo": 1})),
        (
            "json malformado",
            client.post(
                "/tarefas",
                content="{",
                headers={"content-type": "application/json"},
            ),
        ),
        ("id inválido", client.get("/tarefas/abc")),
        ("limite inválido", client.get("/tarefas?limite=0")),
        ("limite textual", client.get("/tarefas?limite=abc")),
        ("deslocamento negativo", client.get("/tarefas?deslocamento=-1")),
        ("filtro inválido", client.get("/tarefas?status=x")),
        ("patch vazio", client.patch(unknown, json={})),
    ]


class TestErrorLanguage:
    def test_every_error_follows_the_contract_in_portuguese(
        self, client: TestClient
    ) -> None:
        for scenario, response in _error_responses(client):
            body = response.json()
            assert set(body) == ERROR_KEYS, scenario
            assert body["codigo"] in KNOWN_CODES, scenario
            assert isinstance(body["detalhes"], list), scenario
            messages = [body["mensagem"]]
            for detail in body["detalhes"]:
                assert set(detail) == DETAIL_KEYS, scenario
                messages += [detail["campo"], detail["mensagem"]]
            for message in messages:
                assert _has_english_marker(message) is None, (scenario, message)

    def test_internal_error_is_in_portuguese(self, app: FastAPI) -> None:
        @app.get("/falha")
        def fail() -> None:
            raise RuntimeError("boom")

        client = TestClient(app, raise_server_exceptions=False)

        body = client.get("/falha").json()

        assert set(body) == ERROR_KEYS
        assert _has_english_marker(body["mensagem"]) is None


def _documentation_strings(schema: dict[str, Any]) -> list[str]:
    """Coleta títulos, resumos, descrições e nomes de tags do esquema."""
    found = [schema["info"]["title"], schema["info"].get("description", "")]
    found += [tag["name"] for tag in schema.get("tags", [])]
    found += [tag.get("description", "") for tag in schema.get("tags", [])]

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in {"summary", "description"} and isinstance(value, str):
                    found.append(value)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(schema["paths"])
    walk(schema.get("components", {}))
    return found


@pytest.fixture
def schema(client: TestClient) -> dict[str, Any]:
    return client.get("/esquema-openapi.json").json()


def _resolve(schema: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    ref = node.get("$ref")
    if ref is None:
        return node
    return schema["components"]["schemas"][ref.rsplit("/", 1)[-1]]


class TestOpenApiLanguage:
    def test_has_no_default_english_texts(self, schema: dict[str, Any]) -> None:
        dumped = json.dumps(schema)

        for forbidden in OPENAPI_FORBIDDEN:
            assert forbidden not in dumped

    def test_documentation_texts_have_no_english_markers(
        self, schema: dict[str, Any]
    ) -> None:
        for text in _documentation_strings(schema):
            assert _has_english_marker(text) is None, text

    def test_patch_is_documented(self, schema: dict[str, Any]) -> None:
        operation = schema["paths"]["/tarefas/{task_id}"]["patch"]

        assert operation["summary"]
        assert operation["responses"]["200"]["description"]

    def test_error_responses_use_the_error_contract(
        self, schema: dict[str, Any]
    ) -> None:
        checked = 0
        for path, methods in schema["paths"].items():
            for method, operation in methods.items():
                has_input = operation.get("parameters") or operation.get("requestBody")
                if not has_input:
                    continue
                response_422 = operation["responses"]["422"]
                content = response_422["content"]["application/json"]["schema"]
                properties = _resolve(schema, content)["properties"]
                assert set(properties) == ERROR_KEYS, (method, path)
                assert response_422["description"], (method, path)
                checked += 1
        assert checked >= 6

    def test_routes_with_id_document_404(self, schema: dict[str, Any]) -> None:
        for method in ("get", "put", "patch", "delete"):
            operation = schema["paths"]["/tarefas/{task_id}"][method]
            content = operation["responses"]["404"]["content"]["application/json"]
            assert set(_resolve(schema, content["schema"])["properties"]) == ERROR_KEYS
