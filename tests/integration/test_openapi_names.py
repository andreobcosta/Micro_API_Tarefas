"""Nomes em português no esquema OpenAPI: componentes, operationId e parâmetro."""

import json
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

COMPONENTS = {
    "Tarefa",
    "CriacaoDeTarefa",
    "SubstituicaoDeTarefa",
    "AtualizacaoDeTarefa",
    "ListaDeTarefas",
    "StatusDaTarefa",
    "Erro",
    "DetalheDoErro",
    "RespostaDeSaude",
}
OPERATION_IDS = {
    ("/saude", "get"): "verificar_saude",
    ("/tarefas", "post"): "criar_tarefa",
    ("/tarefas", "get"): "listar_tarefas",
    ("/tarefas/{id}", "get"): "consultar_tarefa",
    ("/tarefas/{id}", "put"): "substituir_tarefa",
    ("/tarefas/{id}", "patch"): "atualizar_tarefa",
    ("/tarefas/{id}", "delete"): "excluir_tarefa",
}
ENGLISH_NAMES = ["Task", "Error", "Response", "Health", "task_id", "Validation"]
INTERNAL_TERMS = ["by_alias", "Pydantic", "model_fields_set", "inglês", "Protocol"]


@pytest.fixture
def schema(client: TestClient) -> dict[str, Any]:
    return client.get("/esquema-openapi.json").json()


def _refs(node: Any) -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref":
                found.append(value)
            else:
                found += _refs(value)
    elif isinstance(node, list):
        for item in node:
            found += _refs(item)
    return found


def _descriptions(node: Any) -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key in {"description", "summary"} and isinstance(value, str):
                found.append(value)
            found += _descriptions(value)
    elif isinstance(node, list):
        for item in node:
            found += _descriptions(item)
    return found


class TestComponentNames:
    def test_components_have_portuguese_names(self, schema: dict[str, Any]) -> None:
        assert set(schema["components"]["schemas"]) == COMPONENTS

    def test_every_ref_points_to_an_existing_component(
        self, schema: dict[str, Any]
    ) -> None:
        components = set(schema["components"]["schemas"])
        refs = _refs(schema)

        assert refs, "esperava ao menos um $ref no esquema"
        for ref in refs:
            prefix, _, name = ref.rpartition("/")
            assert prefix == "#/components/schemas", ref
            assert name in components, ref

    def test_component_titles_follow_the_new_names(
        self, schema: dict[str, Any]
    ) -> None:
        for name, component in schema["components"]["schemas"].items():
            assert component.get("title", name) == name

    def test_no_english_names_remain(self, schema: dict[str, Any]) -> None:
        names = list(schema["components"]["schemas"])
        names += [
            op["operationId"] for ms in schema["paths"].values() for op in ms.values()
        ]
        names += list(schema["paths"])

        for name in names:
            for english in ENGLISH_NAMES:
                assert english not in name, (english, name)


class TestOperations:
    def test_operation_ids_are_explicit_and_in_portuguese(
        self, schema: dict[str, Any]
    ) -> None:
        found = {
            (path, method): operation["operationId"]
            for path, methods in schema["paths"].items()
            for method, operation in methods.items()
        }

        assert found == OPERATION_IDS

    def test_path_parameter_is_named_id(self, schema: dict[str, Any]) -> None:
        for method in ("get", "put", "patch", "delete"):
            parameters = schema["paths"]["/tarefas/{id}"][method]["parameters"]
            assert [(p["name"], p["in"]) for p in parameters] == [("id", "path")]

    def test_documentation_has_no_internal_terms(self, schema: dict[str, Any]) -> None:
        for text in _descriptions(schema):
            for term in INTERNAL_TERMS:
                assert term not in text, (term, text)


class TestDocumentationPages:
    @pytest.mark.parametrize(
        "url", ["/documentacao", "/referencia", "/esquema-openapi.json"]
    )
    def test_page_responds_200(self, client: TestClient, url: str) -> None:
        assert client.get(url).status_code == 200

    def test_schema_is_generated_once_and_stable(self, app: FastAPI) -> None:
        first = app.openapi()
        second = app.openapi()

        assert first is second
        assert json.dumps(first) == json.dumps(second)
        assert set(first["components"]["schemas"]) == COMPONENTS

    def test_schemas_of_independent_apps_are_equal(self) -> None:
        from app.main import create_app

        assert create_app().openapi() == create_app().openapi()
