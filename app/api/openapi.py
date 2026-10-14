"""Esquema OpenAPI com os nomes dos componentes em português."""

from typing import Any

from fastapi import FastAPI

from app.core import messages

_REF_PREFIX = "#/components/schemas/"


def _rewrite_refs(node: Any, names: dict[str, str]) -> None:
    """Reescreve, no próprio objeto, todo `$ref` que aponta para um componente renomeado."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith(_REF_PREFIX):
            old = ref.removeprefix(_REF_PREFIX)
            node["$ref"] = _REF_PREFIX + names.get(old, old)
        for value in node.values():
            _rewrite_refs(value, names)
    elif isinstance(node, list):
        for item in node:
            _rewrite_refs(item, names)


def localize_schema(schema: dict[str, Any], names: dict[str, str]) -> dict[str, Any]:
    """Renomeia os componentes (e seus `title`) e reescreve os `$ref` do esquema."""
    components = schema.get("components", {}).get("schemas", {})
    renamed = {}
    for old, component in components.items():
        new = names.get(old, old)
        if component.get("title") == old:
            component["title"] = new
        renamed[new] = component
    if components:
        schema["components"]["schemas"] = renamed
    _rewrite_refs(schema, names)
    return schema


def install_portuguese_openapi(app: FastAPI) -> None:
    """Faz `app.openapi()` devolver o esquema com nomes em português (em cache)."""
    generate = app.openapi

    def openapi() -> dict[str, Any]:
        if app.openapi_schema is None:
            app.openapi_schema = localize_schema(
                generate(), messages.OPENAPI_COMPONENT_NAMES
            )
        return app.openapi_schema

    app.openapi = openapi  # type: ignore[method-assign]
