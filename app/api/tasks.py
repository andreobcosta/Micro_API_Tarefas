"""Rotas de tarefas: convertem HTTP <-> schemas e chamam o `TaskService`."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.api.dependencies import get_task_service
from app.core import messages
from app.models.task import TaskStatus
from app.schemas.error import ErrorResponse
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskReplace,
    TaskResponse,
    TaskUpdate,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/tarefas", tags=[messages.TAG_TASKS])

Service = Annotated[TaskService, Depends(get_task_service)]
# O parâmetro de rota aparece como `id` no contrato (alias), e `task_id` no código.
TaskId = Annotated[uuid.UUID, Path(alias="id", description=messages.PARAM_TASK_ID)]

VALIDATION_ERROR: dict[int | str, dict[str, Any]] = {
    422: {"model": ErrorResponse, "description": messages.RESPONSE_VALIDATION_ERROR}
}
NOT_FOUND: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse, "description": messages.TASK_NOT_FOUND}
}


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id=messages.OPERATION_ID_CREATE_TASK,
    summary=messages.SUMMARY_CREATE_TASK,
    description=messages.DESCRIPTION_CREATE_TASK,
    response_description=messages.RESPONSE_CREATE_TASK,
    responses=VALIDATION_ERROR,
)
def create_task(data: TaskCreate, service: Service) -> TaskResponse:
    """Cria uma tarefa."""
    return TaskResponse.model_validate(service.create(data))


@router.get(
    "",
    response_model=TaskListResponse,
    operation_id=messages.OPERATION_ID_LIST_TASKS,
    summary=messages.SUMMARY_LIST_TASKS,
    description=messages.DESCRIPTION_LIST_TASKS,
    response_description=messages.RESPONSE_LIST_TASKS,
    responses=VALIDATION_ERROR,
)
def list_tasks(
    service: Service,
    status_filter: Annotated[
        TaskStatus | None, Query(alias="status", description=messages.PARAM_STATUS)
    ] = None,
    limit: Annotated[
        int, Query(alias="limite", ge=1, le=100, description=messages.PARAM_LIMIT)
    ] = 10,
    offset: Annotated[
        int, Query(alias="deslocamento", ge=0, description=messages.PARAM_OFFSET)
    ] = 0,
) -> TaskListResponse:
    """Lista tarefas com filtro por status e paginação."""
    tasks, total = service.list(status_filter, limit, offset)
    return TaskListResponse(
        items=[TaskResponse.model_validate(task) for task in tasks],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{id}",
    response_model=TaskResponse,
    operation_id=messages.OPERATION_ID_GET_TASK,
    summary=messages.SUMMARY_GET_TASK,
    description=messages.DESCRIPTION_GET_TASK,
    response_description=messages.RESPONSE_GET_TASK,
    responses={**NOT_FOUND, **VALIDATION_ERROR},
)
def get_task(task_id: TaskId, service: Service) -> TaskResponse:
    """Consulta uma tarefa pelo id."""
    return TaskResponse.model_validate(service.get(task_id))


@router.put(
    "/{id}",
    response_model=TaskResponse,
    operation_id=messages.OPERATION_ID_REPLACE_TASK,
    summary=messages.SUMMARY_REPLACE_TASK,
    description=messages.DESCRIPTION_REPLACE_TASK,
    response_description=messages.RESPONSE_REPLACE_TASK,
    responses={**NOT_FOUND, **VALIDATION_ERROR},
)
def replace_task(task_id: TaskId, data: TaskReplace, service: Service) -> TaskResponse:
    """Substitui uma tarefa (PUT)."""
    return TaskResponse.model_validate(service.replace(task_id, data))


@router.patch(
    "/{id}",
    response_model=TaskResponse,
    operation_id=messages.OPERATION_ID_UPDATE_TASK,
    summary=messages.SUMMARY_UPDATE_TASK,
    description=messages.DESCRIPTION_UPDATE_TASK,
    response_description=messages.RESPONSE_UPDATE_TASK,
    responses={**NOT_FOUND, **VALIDATION_ERROR},
)
def update_task(task_id: TaskId, data: TaskUpdate, service: Service) -> TaskResponse:
    """Altera só os campos enviados (PATCH)."""
    return TaskResponse.model_validate(service.update(task_id, data))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id=messages.OPERATION_ID_DELETE_TASK,
    summary=messages.SUMMARY_DELETE_TASK,
    description=messages.DESCRIPTION_DELETE_TASK,
    response_description=messages.RESPONSE_DELETE_TASK,
    responses={**NOT_FOUND, **VALIDATION_ERROR},
)
def delete_task(task_id: TaskId, service: Service) -> Response:
    """Exclui uma tarefa."""
    service.delete(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
