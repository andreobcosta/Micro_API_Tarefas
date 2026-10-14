"""Criação do engine, das sessões e das tabelas."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base


def _is_in_memory_sqlite(url: str) -> bool:
    parsed = make_url(url)
    return parsed.get_backend_name() == "sqlite" and parsed.database in (
        None,
        "",
        ":memory:",
    )


def create_db_engine(url: str) -> Engine:
    """Cria o engine a partir da URL, com ajustes para SQLite.

    SQLite em memória usa `StaticPool` (uma única conexão compartilhada, para
    o banco não sumir entre sessões); SQLite em arquivo libera o uso entre
    threads (`check_same_thread=False`), como o servidor faz.
    """
    if not url.startswith("sqlite"):
        return create_engine(url)
    if _is_in_memory_sqlite(url):
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
