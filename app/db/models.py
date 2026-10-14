"""Modelo ORM da tabela `tasks` (estilo SQLAlchemy 2.x)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.core import messages


class UtcDateTime(TypeDecorator[datetime]):
    """Data/hora sempre em UTC com fuso.

    O SQLite não guarda fuso: gravamos o instante convertido para UTC e, na
    leitura, devolvemos a data com `tzinfo=UTC`.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        """Converte para UTC e remove o fuso antes de gravar."""
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError(messages.NAIVE_DATETIME)
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        """Devolve a data lida com `tzinfo=UTC`."""
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)


class Base(DeclarativeBase):
    """Base declarativa dos modelos."""


class TaskModel(Base):
    """Linha da tabela `tasks`. O `status` guarda o VALOR do enum (texto)."""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, index=True)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime)
