"""Testes do tipo `UtcDateTime` e da coluna obrigatória `created_at`."""

import uuid
from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import TaskModel, UtcDateTime
from app.db.session import create_db_engine, create_session_factory, create_tables


@pytest.fixture
def engine() -> Iterator[Engine]:
    engine = create_db_engine("sqlite://")
    create_tables(engine)
    yield engine
    engine.dispose()


def test_none_passes_through_in_both_directions(engine: Engine) -> None:
    column_type = UtcDateTime()

    assert column_type.process_bind_param(None, engine.dialect) is None
    assert column_type.process_result_value(None, engine.dialect) is None


def test_naive_datetime_is_rejected_on_bind(engine: Engine) -> None:
    with pytest.raises(ValueError):
        UtcDateTime().process_bind_param(datetime(2026, 1, 1), engine.dialect)


def test_null_created_at_is_refused_and_no_row_is_written(engine: Engine) -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    factory = create_session_factory(engine)

    with factory() as session:
        session.add(
            TaskModel(
                id=uuid.uuid4(),
                title="Sem data",
                description=None,
                status="pendente",
                created_at=None,  # type: ignore[arg-type]
                updated_at=now,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()

    with factory() as session:
        assert _count(session) == 0


def _count(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(TaskModel)) or 0
