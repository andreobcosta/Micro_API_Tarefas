"""Suíte de contrato de `TaskRepository`, executada em todas as implementações."""

import uuid
from collections.abc import Iterator
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import app.repositories.base as base_module
import app.repositories.in_memory as in_memory_module
from app.models.task import Task, TaskStatus
from app.repositories.base import TaskRepository
from app.db.session import create_db_engine, create_session_factory, create_tables
from app.repositories.in_memory import InMemoryTaskRepository
from app.repositories.sql_repository import SqlTaskRepository

BASE_TIME = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def make_task(
    minutes: int = 0,
    status: TaskStatus = TaskStatus.PENDING,
    title: str = "Estudar pytest",
    description: str | None = None,
) -> Task:
    """Cria uma tarefa com data explícita (BASE_TIME + `minutes`)."""
    moment = BASE_TIME + timedelta(minutes=minutes)
    return Task(
        id=uuid.uuid4(),
        title=title,
        description=description,
        status=status,
        created_at=moment,
        updated_at=moment,
    )


@pytest.fixture(params=["in_memory", "sql"])
def repository(request: pytest.FixtureRequest) -> Iterator[TaskRepository]:
    """Uma instância nova de cada implementação (banco SQL em memória isolado)."""
    if request.param == "in_memory":
        yield InMemoryTaskRepository()
        return
    engine = create_db_engine("sqlite://")
    create_tables(engine)
    yield SqlTaskRepository(create_session_factory(engine))
    engine.dispose()


class TestAddAndGet:
    def test_get_returns_added_task(self, repository: TaskRepository) -> None:
        task = make_task()

        repository.add(task)

        assert repository.get(task.id) == task

    def test_add_returns_the_stored_task(self, repository: TaskRepository) -> None:
        task = make_task()

        assert repository.add(task) == task

    def test_get_returns_none_for_unknown_id(self, repository: TaskRepository) -> None:
        assert repository.get(uuid.uuid4()) is None


class TestList:
    def test_empty_repository_returns_no_items_and_zero_total(
        self, repository: TaskRepository
    ) -> None:
        assert repository.list(status=None, limit=10, offset=0) == ([], 0)

    def test_orders_by_created_at_descending(self, repository: TaskRepository) -> None:
        oldest, middle, newest = make_task(1), make_task(2), make_task(3)
        for task in (middle, newest, oldest):
            repository.add(task)

        items, total = repository.list(status=None, limit=10, offset=0)

        assert [t.id for t in items] == [newest.id, middle.id, oldest.id]
        assert total == 3

    def test_total_reflects_status_filter(self, repository: TaskRepository) -> None:
        repository.add(make_task(1, TaskStatus.PENDING))
        repository.add(make_task(2, TaskStatus.DONE))
        repository.add(make_task(3, TaskStatus.DONE))

        items, total = repository.list(status=TaskStatus.DONE, limit=10, offset=0)

        assert total == 2
        assert {t.status for t in items} == {TaskStatus.DONE}

    def test_filter_without_matches_returns_empty(
        self, repository: TaskRepository
    ) -> None:
        repository.add(make_task(1, TaskStatus.PENDING))

        assert repository.list(TaskStatus.DONE, limit=10, offset=0) == ([], 0)

    def test_paginates_last_page_with_remaining_items(
        self, repository: TaskRepository
    ) -> None:
        for minute in range(25):
            repository.add(make_task(minute))

        items, total = repository.list(status=None, limit=10, offset=20)

        assert len(items) == 5
        assert total == 25
        assert items[0].created_at == BASE_TIME + timedelta(minutes=4)
        assert items[-1].created_at == BASE_TIME

    def test_limit_caps_the_page_size(self, repository: TaskRepository) -> None:
        for minute in range(25):
            repository.add(make_task(minute))

        items, total = repository.list(status=None, limit=10, offset=0)

        assert len(items) == 10
        assert total == 25

    def test_offset_beyond_total_returns_empty_items_with_total(
        self, repository: TaskRepository
    ) -> None:
        for minute in range(3):
            repository.add(make_task(minute))

        assert repository.list(status=None, limit=10, offset=50) == ([], 3)

    def test_same_created_at_is_ordered_by_id_descending(
        self, repository: TaskRepository
    ) -> None:
        tasks = [make_task(5) for _ in range(5)]
        for task in tasks:
            repository.add(task)

        items, _ = repository.list(status=None, limit=10, offset=0)

        expected = sorted((t.id for t in tasks), reverse=True)
        assert [t.id for t in items] == expected

    def test_pagination_with_same_created_at_has_no_overlap(
        self, repository: TaskRepository
    ) -> None:
        for _ in range(6):
            repository.add(make_task(5))

        first, _ = repository.list(status=None, limit=3, offset=0)
        second, _ = repository.list(status=None, limit=3, offset=3)

        ids = [t.id for t in first + second]
        assert len(set(ids)) == 6


class TestUpdate:
    def test_update_persists_changes_and_returns_true(
        self, repository: TaskRepository
    ) -> None:
        task = make_task()
        repository.add(task)

        changed = replace(task, title="Novo título", status=TaskStatus.DONE)

        assert repository.update(changed) is True
        assert repository.get(task.id) == changed

    def test_update_unknown_id_returns_false_and_stores_nothing(
        self, repository: TaskRepository
    ) -> None:
        ghost = make_task()

        assert repository.update(ghost) is False
        assert repository.get(ghost.id) is None
        assert repository.list(status=None, limit=10, offset=0) == ([], 0)


class TestDelete:
    def test_delete_removes_task_and_returns_true(
        self, repository: TaskRepository
    ) -> None:
        task = make_task()
        repository.add(task)

        assert repository.delete(task.id) is True
        assert repository.get(task.id) is None

    def test_delete_unknown_id_returns_false(self, repository: TaskRepository) -> None:
        assert repository.delete(uuid.uuid4()) is False

    def test_delete_twice_returns_false_the_second_time(
        self, repository: TaskRepository
    ) -> None:
        task = make_task()
        repository.add(task)
        repository.delete(task.id)

        assert repository.delete(task.id) is False


class TestIsolation:
    """Decisão: o repositório guarda e devolve cópias, nunca a mesma referência."""

    def test_mutating_the_added_object_does_not_change_the_stored_one(
        self, repository: TaskRepository
    ) -> None:
        task = make_task(title="Original")
        repository.add(task)

        task.title = "Alterado por fora"

        stored = repository.get(task.id)
        assert stored is not None
        assert stored.title == "Original"

    def test_mutating_the_object_from_get_does_not_change_the_stored_one(
        self, repository: TaskRepository
    ) -> None:
        task = make_task(title="Original")
        repository.add(task)
        fetched = repository.get(task.id)
        assert fetched is not None

        fetched.title = "Alterado por fora"

        stored = repository.get(task.id)
        assert stored is not None
        assert stored.title == "Original"

    def test_mutating_items_from_list_does_not_change_the_stored_ones(
        self, repository: TaskRepository
    ) -> None:
        task = make_task(title="Original")
        repository.add(task)
        items, _ = repository.list(status=None, limit=10, offset=0)

        items[0].title = "Alterado por fora"

        stored = repository.get(task.id)
        assert stored is not None
        assert stored.title == "Original"

    def test_mutating_the_object_passed_to_update_does_not_change_the_stored_one(
        self, repository: TaskRepository
    ) -> None:
        task = make_task(title="Original")
        repository.add(task)
        changed = replace(task, title="Salvo")
        repository.update(changed)

        changed.title = "Alterado depois do update"

        stored = repository.get(task.id)
        assert stored is not None
        assert stored.title == "Salvo"


class TestContract:
    def test_implementation_satisfies_the_protocol(
        self, repository: TaskRepository
    ) -> None:
        assert repository.get(uuid.uuid4()) is None

    @pytest.mark.parametrize("module", [base_module, in_memory_module])
    def test_modules_do_not_import_web_or_orm_frameworks(self, module: object) -> None:
        source = Path(module.__file__).read_text(encoding="utf-8")  # type: ignore[attr-defined]

        assert "fastapi" not in source.lower()
        assert "sqlalchemy" not in source.lower()
