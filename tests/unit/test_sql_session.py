"""Testes da criação do engine: só SQLite é aceito no MVP (ADR-0002)."""

from pathlib import Path

import pytest

from app.core.config import SettingsError
from app.db.session import create_db_engine


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://usuario:segredo@host/db",
        "mysql://usuario:segredo@host/db",
        "isto não é uma url com segredo",
        "",
    ],
)
def test_non_sqlite_or_malformed_url_is_rejected_without_echoing_it(
    url: str,
) -> None:
    with pytest.raises(SettingsError) as error:
        create_db_engine(url)

    message = str(error.value)
    assert "DATABASE_URL" in message
    assert "SQLite" in message
    assert "segredo" not in message
    assert "usuario" not in message
    assert url not in message or url == ""


def test_error_message_is_in_portuguese() -> None:
    with pytest.raises(SettingsError) as error:
        create_db_engine("postgresql://usuario:segredo@host/db")

    assert "não é suportado" in str(error.value)


def test_memory_url_is_accepted() -> None:
    engine = create_db_engine("sqlite://")

    assert engine.dialect.name == "sqlite"
    engine.dispose()


def test_file_url_is_accepted_and_does_not_create_the_file_until_used(
    tmp_path: Path,
) -> None:
    path = tmp_path / "x.db"

    engine = create_db_engine(f"sqlite:///{path}")

    assert engine.dialect.name == "sqlite"
    assert not path.exists()
    engine.dispose()
