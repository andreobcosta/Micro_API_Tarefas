"""Testes unitários do `TaskService` com repositório em memória e relógio falso."""

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import app.services.task_service as task_service_module
from app.core import messages
from app.core.errors import TaskNotFoundError
from app.models.task import Task, TaskStatus
from app.repositories.in_memory import InMemoryTaskRepository
from app.schemas.task import TaskCreate, TaskReplace, TaskUpdate
from app.services.task_service import TaskService

START = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class FakeClock:
    """Relógio controlável: cada `advance` move o tempo para frente."""

    def __init__(self) -> None:
        self.current = START

    def __call__(self) -> datetime:
        return self.current

    def advance(self, minutes: int = 1) -> None:
        self.current += timedelta(minutes=minutes)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def repository() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()


@pytest.fixture
def service(repository: InMemoryTaskRepository, clock: FakeClock) -> TaskService:
    return TaskService(repository, clock=clock)


def _create(service: TaskService, **payload: object):
    return service.create(TaskCreate.model_validate({"titulo": "Estudar", **payload}))


class TestCreate:
    def test_generates_uuid_and_default_status(self, service: TaskService) -> None:
        task = _create(service)

        assert isinstance(task.id, uuid.UUID)
        assert task.id.version == 4
        assert task.status is TaskStatus.PENDING
        assert task.title == "Estudar"
        assert task.description is None

    def test_sets_created_at_equal_to_updated_at_from_clock(
        self, service: TaskService
    ) -> None:
        task = _create(service)

        assert task.created_at == START
        assert task.updated_at == START

    def test_persists_the_task(
        self, service: TaskService, repository: InMemoryTaskRepository
    ) -> None:
        task = _create(service, descricao="Detalhe", status="em_andamento")

        assert repository.get(task.id) == task
        assert task.description == "Detalhe"
        assert task.status is TaskStatus.IN_PROGRESS

    def test_each_task_gets_a_distinct_id(self, service: TaskService) -> None:
        assert _create(service).id != _create(service).id

    def test_default_clock_produces_timezone_aware_utc_dates(self) -> None:
        service = TaskService(InMemoryTaskRepository())

        task = _create(service)

        assert task.created_at.utcoffset() == timedelta(0)
        assert task.updated_at.utcoffset() == timedelta(0)


class TestGet:
    def test_returns_existing_task(self, service: TaskService) -> None:
        created = _create(service)

        assert service.get(created.id) == created

    def test_unknown_id_raises_not_found_with_central_message(
        self, service: TaskService
    ) -> None:
        with pytest.raises(TaskNotFoundError) as exc_info:
            service.get(uuid.uuid4())

        assert str(exc_info.value) == messages.TASK_NOT_FOUND


class TestList:
    def test_returns_items_and_total_newest_first(
        self, service: TaskService, clock: FakeClock
    ) -> None:
        first = _create(service, titulo="Primeira")
        clock.advance()
        second = _create(service, titulo="Segunda")

        items, total = service.list(status=None, limit=10, offset=0)

        assert [t.id for t in items] == [second.id, first.id]
        assert total == 2

    def test_forwards_status_limit_and_offset(
        self, service: TaskService, clock: FakeClock
    ) -> None:
        for index in range(5):
            _create(service, titulo=f"Tarefa {index}", status="concluida")
            clock.advance()
        _create(service, titulo="Outra", status="pendente")

        items, total = service.list(status=TaskStatus.DONE, limit=2, offset=3)

        assert total == 5
        assert [t.title for t in items] == ["Tarefa 1", "Tarefa 0"]

    def test_empty_repository(self, service: TaskService) -> None:
        assert service.list(status=None, limit=10, offset=0) == ([], 0)


class TestReplace:
    def test_replaces_all_fields_and_refreshes_updated_at(
        self, service: TaskService, clock: FakeClock
    ) -> None:
        created = _create(service, descricao="Antiga")
        clock.advance(5)

        replaced = service.replace(
            created.id,
            TaskReplace.model_validate({"titulo": "Novo", "status": "concluida"}),
        )

        assert replaced.title == "Novo"
        assert replaced.status is TaskStatus.DONE
        assert replaced.updated_at == START + timedelta(minutes=5)
        assert replaced.updated_at > created.updated_at

    def test_absent_description_becomes_none(
        self, service: TaskService, clock: FakeClock
    ) -> None:
        created = _create(service, descricao="Antiga")
        clock.advance()

        replaced = service.replace(
            created.id,
            TaskReplace.model_validate({"titulo": "Novo", "status": "pendente"}),
        )

        assert replaced.description is None

    def test_keeps_id_and_created_at(
        self, service: TaskService, clock: FakeClock
    ) -> None:
        created = _create(service)
        clock.advance(10)

        replaced = service.replace(
            created.id,
            TaskReplace.model_validate({"titulo": "Novo", "status": "pendente"}),
        )

        assert replaced.id == created.id
        assert replaced.created_at == created.created_at

    def test_persists_the_change(
        self, service: TaskService, repository: InMemoryTaskRepository
    ) -> None:
        created = _create(service)

        replaced = service.replace(
            created.id,
            TaskReplace.model_validate({"titulo": "Novo", "status": "concluida"}),
        )

        assert repository.get(created.id) == replaced

    def test_unknown_id_raises_not_found_and_stores_nothing(
        self, service: TaskService, repository: InMemoryTaskRepository
    ) -> None:
        ghost_id = uuid.uuid4()

        with pytest.raises(TaskNotFoundError):
            service.replace(
                ghost_id,
                TaskReplace.model_validate({"titulo": "Novo", "status": "pendente"}),
            )

        assert repository.get(ghost_id) is None


class TestUpdate:
    def test_changes_only_the_sent_field(
        self, service: TaskService, clock: FakeClock
    ) -> None:
        created = _create(service, descricao="Detalhe")
        clock.advance(3)

        updated = service.update(
            created.id, TaskUpdate.model_validate({"status": "em_andamento"})
        )

        assert updated.status is TaskStatus.IN_PROGRESS
        assert updated.title == "Estudar"
        assert updated.description == "Detalhe"
        assert updated.updated_at == START + timedelta(minutes=3)
        assert updated.updated_at > created.updated_at

    def test_null_description_clears_it(
        self, service: TaskService, clock: FakeClock
    ) -> None:
        created = _create(service, descricao="Detalhe")
        clock.advance()

        updated = service.update(
            created.id, TaskUpdate.model_validate({"descricao": None})
        )

        assert updated.description is None
        assert updated.title == "Estudar"
        assert updated.status is TaskStatus.PENDING

    def test_absent_description_is_kept(
        self, service: TaskService, clock: FakeClock
    ) -> None:
        created = _create(service, descricao="Detalhe")
        clock.advance()

        updated = service.update(
            created.id, TaskUpdate.model_validate({"titulo": "Novo"})
        )

        assert updated.title == "Novo"
        assert updated.description == "Detalhe"

    def test_keeps_id_and_created_at(
        self, service: TaskService, clock: FakeClock
    ) -> None:
        created = _create(service)
        clock.advance(10)

        updated = service.update(
            created.id, TaskUpdate.model_validate({"titulo": "Novo"})
        )

        assert updated.id == created.id
        assert updated.created_at == created.created_at

    def test_persists_the_change(
        self, service: TaskService, repository: InMemoryTaskRepository
    ) -> None:
        created = _create(service)

        updated = service.update(
            created.id, TaskUpdate.model_validate({"titulo": "Novo"})
        )

        assert repository.get(created.id) == updated

    def test_unknown_id_raises_not_found(self, service: TaskService) -> None:
        with pytest.raises(TaskNotFoundError):
            service.update(uuid.uuid4(), TaskUpdate.model_validate({"titulo": "Novo"}))


class TestConcurrentRemoval:
    def test_task_removed_between_get_and_update_raises_not_found(
        self, clock: FakeClock
    ) -> None:
        class VanishingRepository(InMemoryTaskRepository):
            """Simula a tarefa ser removida logo antes da gravação."""

            def update(self, task: Task) -> bool:
                self.delete(task.id)
                return super().update(task)

        service = TaskService(VanishingRepository(), clock=clock)
        created = _create(service)

        with pytest.raises(TaskNotFoundError):
            service.update(created.id, TaskUpdate.model_validate({"titulo": "Novo"}))


class TestDelete:
    def test_removes_the_task(self, service: TaskService) -> None:
        created = _create(service)

        service.delete(created.id)

        with pytest.raises(TaskNotFoundError):
            service.get(created.id)

    def test_unknown_id_raises_not_found(self, service: TaskService) -> None:
        with pytest.raises(TaskNotFoundError):
            service.delete(uuid.uuid4())

    def test_second_delete_raises_not_found(self, service: TaskService) -> None:
        created = _create(service)
        service.delete(created.id)

        with pytest.raises(TaskNotFoundError):
            service.delete(created.id)


class TestErrors:
    def test_task_not_found_message_comes_from_central_messages(self) -> None:
        assert str(TaskNotFoundError()) == messages.TASK_NOT_FOUND
        assert messages.TASK_NOT_FOUND == "Tarefa não encontrada."

    def test_domain_errors_are_plain_exceptions(self) -> None:
        assert issubclass(TaskNotFoundError, Exception)


def test_service_module_does_not_import_web_or_orm_frameworks() -> None:
    source = Path(task_service_module.__file__).read_text(encoding="utf-8")

    assert "fastapi" not in source.lower()
    assert "sqlalchemy" not in source.lower()
