"""Testes de contrato dos esquemas Pydantic (aliases em português)."""

import uuid
from datetime import datetime, timezone
from typing import Any

import pytest
from pydantic import ValidationError

from app.core import messages
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskReplace, TaskResponse, TaskUpdate


def _errors(exc_info: pytest.ExceptionInfo[ValidationError]) -> list[tuple[str, tuple]]:
    """Reduz os erros do Pydantic a pares (tipo, loc), sem depender do texto."""
    return [(e["type"], e["loc"]) for e in exc_info.value.errors()]


def _make_task(**overrides: Any) -> Task:
    now = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
    data: dict[str, Any] = {
        "id": uuid.uuid4(),
        "title": "Estudar pytest",
        "description": "Capítulo 3",
        "status": TaskStatus.PENDING,
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    return Task(**data)


class TestTaskStatus:
    def test_values_are_in_portuguese(self) -> None:
        assert TaskStatus.PENDING.value == "pendente"
        assert TaskStatus.IN_PROGRESS.value == "em_andamento"
        assert TaskStatus.DONE.value == "concluida"

    def test_has_only_three_members(self) -> None:
        assert len(TaskStatus) == 3


class TestTaskCreate:
    def test_accepts_minimal_payload_with_default_status(self) -> None:
        task = TaskCreate.model_validate({"titulo": "Estudar pytest"})

        assert task.title == "Estudar pytest"
        assert task.description is None
        assert task.status is TaskStatus.PENDING

    def test_accepts_full_payload_by_alias(self) -> None:
        task = TaskCreate.model_validate(
            {"titulo": "Estudar", "descricao": "Detalhe", "status": "em_andamento"}
        )

        assert task.description == "Detalhe"
        assert task.status is TaskStatus.IN_PROGRESS

    def test_accepts_internal_names_via_populate_by_name(self) -> None:
        task = TaskCreate(title="Estudar", description="Detalhe")

        assert task.title == "Estudar"
        assert task.description == "Detalhe"

    def test_strips_whitespace_from_title(self) -> None:
        task = TaskCreate.model_validate({"titulo": "   Estudar   "})

        assert task.title == "Estudar"

    @pytest.mark.parametrize("title", ["abc", "a" * 100])
    def test_title_length_boundaries_are_accepted(self, title: str) -> None:
        assert TaskCreate.model_validate({"titulo": title}).title == title

    def test_title_with_two_chars_is_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate.model_validate({"titulo": "ab"})

        assert _errors(exc_info) == [("string_too_short", ("titulo",))]

    def test_title_with_101_chars_is_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate.model_validate({"titulo": "a" * 101})

        assert _errors(exc_info) == [("string_too_long", ("titulo",))]

    def test_title_with_only_spaces_is_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate.model_validate({"titulo": "      "})

        assert _errors(exc_info) == [("string_too_short", ("titulo",))]

    def test_title_is_required(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate.model_validate({})

        assert _errors(exc_info) == [("missing", ("titulo",))]

    def test_description_of_500_chars_is_accepted(self) -> None:
        task = TaskCreate.model_validate({"titulo": "Estudar", "descricao": "d" * 500})

        assert task.description == "d" * 500

    def test_description_of_501_chars_is_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate.model_validate({"titulo": "Estudar", "descricao": "d" * 501})

        assert _errors(exc_info) == [("string_too_long", ("descricao",))]

    def test_invalid_status_is_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate.model_validate({"titulo": "Estudar", "status": "invalido"})

        assert _errors(exc_info) == [("enum", ("status",))]

    def test_english_enum_name_is_not_accepted_as_status(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate.model_validate({"titulo": "Estudar", "status": "PENDING"})

        assert _errors(exc_info) == [("enum", ("status",))]


class TestTaskReplace:
    def test_requires_title_and_status(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TaskReplace.model_validate({})

        assert sorted(_errors(exc_info)) == [
            ("missing", ("status",)),
            ("missing", ("titulo",)),
        ]

    def test_missing_status_is_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TaskReplace.model_validate({"titulo": "Estudar"})

        assert _errors(exc_info) == [("missing", ("status",))]

    def test_absent_description_becomes_none(self) -> None:
        task = TaskReplace.model_validate({"titulo": "Estudar", "status": "concluida"})

        assert task.description is None
        assert task.status is TaskStatus.DONE

    def test_applies_same_title_rules(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TaskReplace.model_validate({"titulo": "x", "status": "pendente"})

        assert _errors(exc_info) == [("string_too_short", ("titulo",))]


class TestTaskUpdate:
    def test_accepts_single_field(self) -> None:
        update = TaskUpdate.model_validate({"status": "em_andamento"})

        assert update.status is TaskStatus.IN_PROGRESS
        assert update.model_fields_set == {"status"}

    def test_empty_body_is_rejected_with_central_message(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TaskUpdate.model_validate({})

        (error,) = exc_info.value.errors()
        assert error["type"] == "value_error"
        assert error["loc"] == ()
        assert str(error["ctx"]["error"]) == messages.PATCH_EMPTY_BODY

    def test_null_title_is_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TaskUpdate.model_validate({"titulo": None})

        assert _errors(exc_info) == [("string_type", ("titulo",))]

    def test_null_status_is_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TaskUpdate.model_validate({"status": None})

        assert _errors(exc_info) == [("enum", ("status",))]

    def test_null_description_clears_it_and_counts_as_sent(self) -> None:
        update = TaskUpdate.model_validate({"descricao": None})

        assert update.description is None
        assert update.model_fields_set == {"description"}

    def test_applies_same_title_rules(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TaskUpdate.model_validate({"titulo": "x"})

        assert _errors(exc_info) == [("string_too_short", ("titulo",))]


class TestTaskResponse:
    def test_serializes_with_contract_keys_in_portuguese(self) -> None:
        task = _make_task()

        body = TaskResponse.model_validate(task).model_dump(mode="json", by_alias=True)

        assert set(body) == {
            "id",
            "titulo",
            "descricao",
            "status",
            "criado_em",
            "atualizado_em",
        }
        assert body["id"] == str(task.id)
        assert body["titulo"] == "Estudar pytest"
        assert body["descricao"] == "Capítulo 3"
        assert body["status"] == "pendente"

    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (TaskStatus.PENDING, "pendente"),
            (TaskStatus.IN_PROGRESS, "em_andamento"),
            (TaskStatus.DONE, "concluida"),
        ],
    )
    def test_status_serializes_as_portuguese_value(
        self, status: TaskStatus, expected: str
    ) -> None:
        body = TaskResponse.model_validate(_make_task(status=status)).model_dump(
            mode="json", by_alias=True
        )

        assert body["status"] == expected

    def test_internal_english_keys_do_not_leak_into_contract(self) -> None:
        body = TaskResponse.model_validate(_make_task()).model_dump(
            mode="json", by_alias=True
        )

        assert not {"title", "description", "created_at", "updated_at"} & set(body)

    def test_dates_are_serialized_in_utc(self) -> None:
        body = TaskResponse.model_validate(_make_task()).model_dump(
            mode="json", by_alias=True
        )

        assert body["criado_em"].endswith("Z")
        assert body["atualizado_em"].endswith("Z")
