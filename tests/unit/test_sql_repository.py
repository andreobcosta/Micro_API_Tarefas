"""Testes específicos do repositório SQL: fuso UTC, status gravado e persistência."""

import uuid
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import Engine, text

from app.db.session import create_db_engine, create_session_factory, create_tables
from app.models.task import Task, TaskStatus
from app.repositories.sql_repository import SqlTaskRepository

MOMENT = datetime(2026, 3, 10, 15, 30, tzinfo=timezone.utc)


def make_task(**changes: object) -> Task:
    values: dict[str, object] = {
        "id": uuid.uuid4(),
        "title": "Estudar SQL",
        "description": None,
        "status": TaskStatus.IN_PROGRESS,
        "created_at": MOMENT,
        "updated_at": MOMENT,
    }
    values.update(changes)
    return Task(**values)  # type: ignore[arg-type]


@pytest.fixture
def engine() -> Iterator[Engine]:
    engine = create_db_engine("sqlite://")
    create_tables(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def repository(engine: Engine) -> SqlTaskRepository:
    return SqlTaskRepository(create_session_factory(engine))


class TestUtcDates:
    def test_dates_come_back_with_utc_timezone(
        self, repository: SqlTaskRepository
    ) -> None:
        task = make_task()
        repository.add(task)

        stored = repository.get(task.id)

        assert stored is not None
        assert stored.created_at.tzinfo is not None
        assert stored.created_at.utcoffset() == timedelta(0)
        assert stored.created_at == MOMENT
        assert stored.updated_at == MOMENT

    def test_non_utc_offset_is_converted_to_the_same_instant(
        self, repository: SqlTaskRepository, engine: Engine
    ) -> None:
        sao_paulo = timezone(timedelta(hours=-3))
        local = datetime(2026, 3, 10, 12, 30, tzinfo=sao_paulo)
        task = make_task(created_at=local, updated_at=local)
        repository.add(task)

        stored = repository.get(task.id)

        assert stored is not None
        assert stored.created_at == MOMENT
        with engine.connect() as connection:
            raw = connection.execute(text("SELECT created_at FROM tasks")).scalar_one()
        assert "15:30" in str(raw)

    def test_naive_datetime_is_rejected(self, repository: SqlTaskRepository) -> None:
        naive = datetime(2026, 3, 10, 15, 30)

        with pytest.raises(ValueError):
            repository.add(make_task(created_at=naive))


class TestStoredStatus:
    @pytest.mark.parametrize("status", list(TaskStatus))
    def test_status_is_stored_by_value_not_by_name(
        self, repository: SqlTaskRepository, engine: Engine, status: TaskStatus
    ) -> None:
        repository.add(make_task(status=status))

        with engine.connect() as connection:
            raw = connection.execute(text("SELECT status FROM tasks")).scalar_one()

        assert raw == status.value

    def test_status_is_read_back_as_enum(self, repository: SqlTaskRepository) -> None:
        task = make_task(status=TaskStatus.DONE)
        repository.add(task)

        stored = repository.get(task.id)

        assert stored is not None
        assert stored.status is TaskStatus.DONE


class TestPersistence:
    def test_data_survives_a_new_engine_on_the_same_file(self, tmp_path: Path) -> None:
        url = f"sqlite:///{tmp_path / 'tasks.db'}"
        first = create_db_engine(url)
        create_tables(first)
        task = make_task(description="persistida")
        SqlTaskRepository(create_session_factory(first)).add(task)
        first.dispose()

        second = create_db_engine(url)
        create_tables(second)
        stored = SqlTaskRepository(create_session_factory(second)).get(task.id)
        second.dispose()

        assert stored == task

    def test_create_tables_is_idempotent(self, engine: Engine) -> None:
        create_tables(engine)

        assert create_tables(engine) is None

    def test_write_is_committed_per_operation(self, engine: Engine) -> None:
        factory = create_session_factory(engine)
        task = make_task()
        SqlTaskRepository(factory).add(task)

        # Outra sessão (outra instância do repositório) enxerga o dado gravado.
        assert SqlTaskRepository(factory).get(task.id) == task

    def test_duplicate_id_does_not_leave_the_session_broken(
        self, repository: SqlTaskRepository
    ) -> None:
        task = make_task()
        repository.add(task)

        with pytest.raises(Exception):
            repository.add(task)

        assert repository.get(task.id) == task
