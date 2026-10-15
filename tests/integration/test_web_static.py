"""Interface web estática servida em `/app` pela própria API."""

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core import messages

STATIC_DIR = Path(__file__).resolve().parents[2] / "app" / "static"
JS_FILES = sorted(
    path.relative_to(STATIC_DIR).as_posix() for path in STATIC_DIR.glob("js/**/*.js")
)
JAVASCRIPT_TYPES = {"text/javascript", "application/javascript"}
EXISTING_PATHS = {"/saude", "/tarefas", "/tarefas/{id}"}
FORBIDDEN_JS = re.compile(
    r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|\beval\s*\(|new Function"
)


def media_type(client: TestClient, path: str) -> str:
    """Devolve o tipo de mídia da resposta, sem o `charset`."""
    response = client.get(path)
    assert response.status_code == 200, path
    return response.headers["content-type"].split(";")[0].strip()


class TestServeInterface:
    def test_index_is_served_as_html(self, client: TestClient) -> None:
        response = client.get("/app/")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert messages.APP_TITLE in response.text

    def test_path_without_trailing_slash_reaches_index(
        self, client: TestClient
    ) -> None:
        response = client.get("/app")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    def test_stylesheet_has_css_type(self, client: TestClient) -> None:
        assert media_type(client, "/app/style.css") == "text/css"

    def test_there_are_javascript_modules_to_serve(self) -> None:
        assert JS_FILES, "esperado ao menos um módulo em app/static/js/"

    @pytest.mark.parametrize("path", JS_FILES)
    def test_every_javascript_module_has_javascript_type(
        self, client: TestClient, path: str
    ) -> None:
        # Módulos ES exigem um tipo JavaScript; `text/plain` seria recusado.
        assert media_type(client, f"/app/{path}") in JAVASCRIPT_TYPES


class TestErrorContract:
    def test_missing_file_uses_the_error_contract(self, client: TestClient) -> None:
        response = client.get("/app/nao-existe.js")

        assert response.status_code == 404
        assert response.json() == {
            "codigo": messages.CODE_ROUTE_NOT_FOUND,
            "mensagem": messages.ROUTE_NOT_FOUND,
            "detalhes": [],
        }


class TestExistingContractIsUntouched:
    def test_mount_is_not_in_the_openapi_schema(self, client: TestClient) -> None:
        paths = set(client.get("/esquema-openapi.json").json()["paths"])

        assert paths == EXISTING_PATHS

    def test_api_routes_still_answer(self, client: TestClient) -> None:
        assert client.get("/saude").json() == {"status": messages.HEALTH_OK}
        assert client.get("/tarefas").status_code == 200


class TestPageIsCspFriendly:
    """A política `default-src 'self'` bloqueia script e estilo inline."""

    def test_index_declares_the_csp(self) -> None:
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

        assert 'http-equiv="Content-Security-Policy"' in html
        assert "default-src 'self'" in html

    def test_index_has_no_inline_script_or_style(self) -> None:
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

        assert "<style" not in html
        assert not re.search(r"\sstyle\s*=", html)
        assert not re.search(r"<script(?![^>]*\ssrc=)[^>]*>", html)
        assert not re.search(r"\son[a-z]+\s*=", html)

    @pytest.mark.parametrize("path", JS_FILES)
    def test_javascript_never_builds_html_from_strings(self, path: str) -> None:
        source = (STATIC_DIR / path).read_text(encoding="utf-8")

        assert not FORBIDDEN_JS.search(source), path
        assert "setAttribute('style'" not in source
        assert 'setAttribute("style"' not in source
