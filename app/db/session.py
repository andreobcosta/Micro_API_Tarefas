"""Criação do engine, das sessões e das tabelas."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import messages
from app.core.config import SettingsError
from app.db.models import Base


def _parse_sqlite_url(url: str) -> URL:
    """Interpreta a URL e garante que o banco é SQLite.

    A mensagem de erro não repete a URL (ela pode conter usuário e senha).

    Raises:
        SettingsError: Se a URL for malformada ou de outro banco.
    """
    try:
        parsed = make_url(url)
    except ArgumentError:
        raise SettingsError(messages.CONFIG_UNSUPPORTED_DATABASE) from None
    if parsed.get_backend_name() != "sqlite":
        raise SettingsError(messages.CONFIG_UNSUPPORTED_DATABASE)
    return parsed


def _is_in_memory(parsed: URL) -> bool:
    return parsed.database in (None, "", ":memory:")


def create_db_engine(url: str) -> Engine:
    """Cria o engine a partir da URL, com ajustes para SQLite.

    O MVP aceita somente SQLite (ADR-0002). SQLite em memória usa `StaticPool`
    (uma única conexão compartilhada, para o banco não sumir entre sessões);
    SQLite em arquivo libera o uso entre threads (`check_same_thread=False`),
    como o servidor faz.

    Raises:
        SettingsError: Se a URL for malformada ou não for de SQLite.
    """
    if _is_in_memory(_parse_sqlite_url(url)):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(url, connect_args={"check_same_thread": False})


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Fábrica de sessões; `expire_on_commit=False` mantém os objetos legíveis."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_tables(engine: Engine) -> None:
    """Cria as tabelas que ainda não existem (sem migrações)."""
    Base.metadata.create_all(engine)
