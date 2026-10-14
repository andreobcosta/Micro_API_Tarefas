"""Fixtures globais: garantem que nenhum teste use ou crie o `tasks.db` local."""

from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LOCAL_DB = ROOT / "tasks.db"


def _snapshot() -> tuple[bool, int | None]:
    """Existência e `mtime` (ns) do `tasks.db` da raiz."""
    if not LOCAL_DB.exists():
        return (False, None)
    return (True, LOCAL_DB.stat().st_mtime_ns)


@pytest.fixture(autouse=True)
def in_memory_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """Aponta o banco padrão para SQLite em memória em todos os testes."""
    monkeypatch.setenv("DATABASE_URL", "sqlite://")


@pytest.fixture(scope="session", autouse=True)
def guard_local_database() -> Iterator[None]:
    """Falha se a suíte criar ou alterar o `tasks.db` da raiz do projeto.

    Um arquivo que já existia (teste manual) não é problema, desde que a
    suíte não o toque.
    """
    before = _snapshot()
    yield
    after = _snapshot()
    assert after == before, "a suíte criou ou alterou o tasks.db da raiz"
