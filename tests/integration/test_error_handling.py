"""Testes dos handlers globais de erro (contrato `{codigo, mensagem, detalhes}`)."""

import logging
import uuid
from typing import Any

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api import error_handlers

SECRET = "segredo-interno-do-servidor"
ENUM_MESSAGE = "Valor inválido. Valores aceitos: pendente, em_andamento, concluida."
FORBIDDEN_KEYS = {"input", "ctx", "url", "detail", "type", "loc", "msg"}
RANDOM_ID = str(uuid.uuid4())

# (método, url, argumentos do request, campo esperado, mensagem esperada)
VALIDATION_CASES = [
    pytest.param(
        "post", "/tarefas", {"json": {}}, "titulo", "Campo obrigatório.", id="missing"
    ),
    pytest.param(
        "post",
        "/tarefas",
        {"json": {"titulo": "ab"}},
        "titulo",
        "Deve ter no mínimo 3 caracteres.",
        id="string_too_short",
    ),
    pytest.param(
        "post",
        "/tarefas",
        {"json": {"titulo": "x" * 101}},
        "titulo",
        "Deve ter no máximo 100 caracteres.",
        id="string_too_long_title",
    ),
    pytest.param(
        "post",
        "/tarefas",
        {"json": {"titulo": "Estudar", "descricao": "x" * 501}},
        "descricao",
        "Deve ter no máximo 500 caracteres.",
        id="string_too_long_description",
    ),
    pytest.param(
        "post",
        "/tarefas",
        {"json": {"titulo": "Estudar", "status": "feito"}},
        "status",
        ENUM_MESSAGE,
        id="enum_body",
    ),
    pytest.param(
        "post",
        "/tarefas",
        {"json": {"titulo": 123}},
        "titulo",
        "Deve ser um texto.",
        id="string_type",
    ),
    pytest.param(
        "post",
        "/tarefas",
        {"content": '{"titulo":', "headers": {"content-type": "application/json"}},
        "corpo",
        "JSON malformado.",
        id="json_invalid",
    ),
    pytest.param(
        "get",
        "/tarefas/abc",
        {},
        "id",
        "Identificador inválido. Informe um UUID válido.",
        id="uuid_parsing",
    ),
    pytest.param(
        "get",
        "/tarefas?limite=0",
        {},
        "limite",
        "Deve ser maior ou igual a 1.",
        id="greater_than_equal",
    ),
    pytest.param(
        "get",
        "/tarefas?limite=101",
        {},
        "limite",
        "Deve ser menor ou igual a 100.",
        id="less_than_equal",
    ),
    pytest.param(
        "get",
        "/tarefas?limite=abc",
        {},
        "limite",
        "Deve ser um número inteiro.",
        id="int_parsing",
    ),
    pytest.param(
        "get",
        "/tarefas?deslocamento=-1",
        {},
        "deslocamento",
        "Deve ser maior ou igual a 0.",
        id="offset_greater_than_equal",
    ),
    pytest.param(
        "get",
        "/tarefas?status=invalido",
        {},
        "status",
        ENUM_MESSAGE,
        id="enum_query",
    ),
    pytest.param(
        "patch",
        f"/tarefas/{RANDOM_ID}",
        {"json": {}},
        "corpo",
        "Informe ao menos um campo para atualizar.",
        id="value_error",
    ),
]


class TestValidationErrors:
    @pytest.mark.parametrize(
        ("method", "url", "request_args", "field", "message"), VALIDATION_CASES
    )
    def test_translates_each_error_type(
        self,
        client: TestClient,
        method: str,
        url: str,
        request_args: dict[str, Any],
        field: str,
        message: str,
    ) -> None:
        response = client.request(method, url, **request_args)

        assert response.status_code == 422
        assert response.json() == {
            "codigo": "VALIDACAO_INVALIDA",
            "mensagem": "Os dados enviados são inválidos.",
            "detalhes": [{"campo": field, "mensagem": message}],
        }

    def test_reports_every_invalid_field(self, client: TestClient) -> None:
        response = client.post("/tarefas", json={"titulo": "ab", "status": "feito"})

        fields = {d["campo"] for d in response.json()["detalhes"]}
        assert fields == {"titulo", "status"}

    def test_never_echoes_input_or_pydantic_internals(self, client: TestClient) -> None:
        response = client.post("/tarefas", json={"titulo": "MARCADOR-" + "x" * 101})

        assert response.status_code == 422
        assert "MARCADOR" not in response.text
        for detail in response.json()["detalhes"]:
            assert set(detail) == {"campo", "mensagem"}
        assert FORBIDDEN_KEYS.isdisjoint(response.json())


class TestTranslateValidationError:
    def test_unknown_type_falls_back_to_portuguese_message(self) -> None:
        error = {
            "type": "tipo_desconhecido",
            "loc": ("body", "titulo"),
            "msg": "Some English message",
            "input": "valor",
        }

        assert error_handlers.translate_validation_error(error) == {
            "campo": "titulo",
            "mensagem": "Valor inválido.",
        }

    def test_known_type_without_required_context_falls_back(self) -> None:
        error = {"type": "string_too_short", "loc": ("body", "titulo")}

        assert error_handlers.translate_validation_error(error) == {
            "campo": "titulo",
            "mensagem": "Valor inválido.",
        }

    def test_value_error_without_context_falls_back(self) -> None:
        error = {"type": "value_error", "loc": ("body",), "msg": "Value error, x"}

        assert error_handlers.translate_validation_error(error) == {
            "campo": "corpo",
            "mensagem": "Valor inválido.",
        }

    def test_nested_location_is_joined_with_dots(self) -> None:
        error = {"type": "missing", "loc": ("body", "itens", 0, "titulo")}

        detail = error_handlers.translate_validation_error(error)

        assert detail["campo"] == "itens.0.titulo"


class TestRouteErrors:
    def test_unknown_route_returns_404_in_portuguese(self, client: TestClient) -> None:
        response = client.get("/nao-existe")

        assert response.status_code == 404
        assert response.json() == {
            "codigo": "ROTA_NAO_ENCONTRADA",
            "mensagem": "Rota não encontrada.",
            "detalhes": [],
        }

    def test_method_not_allowed_returns_405_and_keeps_allow_header(
        self, client: TestClient
    ) -> None:
        response = client.put("/tarefas", json={})

        assert response.status_code == 405
        assert response.json() == {
            "codigo": "METODO_NAO_PERMITIDO",
            "mensagem": "Método não permitido para esta rota.",
            "detalhes": [],
        }
        assert "allow" in response.headers


@pytest.fixture
def failing_client(app: FastAPI) -> TestClient:
    """Cliente cuja aplicação tem rotas que falham de propósito."""

    @app.get("/falha")
    def fail() -> None:
        raise RuntimeError(SECRET)

    @app.get("/proibido")
    def forbidden() -> None:
        raise HTTPException(status_code=403, detail="Forbidden")

    return TestClient(app, raise_server_exceptions=False)


class TestUnexpectedErrors:
    def test_unhandled_exception_returns_generic_500(
        self, failing_client: TestClient
    ) -> None:
        response = failing_client.get("/falha")

        assert response.status_code == 500
        assert response.json() == {
            "codigo": "ERRO_INTERNO",
            "mensagem": "Erro interno do servidor. Tente novamente mais tarde.",
            "detalhes": [],
        }
        assert SECRET not in response.text
        assert "Traceback" not in response.text

    def test_unhandled_exception_is_logged_in_portuguese(
        self, failing_client: TestClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.ERROR):
            failing_client.get("/falha")

        assert any(
            "Erro interno não tratado" in record.getMessage()
            for record in caplog.records
        )

    def test_other_http_errors_use_generic_portuguese_message(
        self, failing_client: TestClient
    ) -> None:
        response = failing_client.get("/proibido")

        assert response.status_code == 403
        assert response.json() == {
            "codigo": "ERRO_HTTP",
            "mensagem": "Não foi possível processar a requisição.",
            "detalhes": [],
        }
        assert "Forbidden" not in response.text
