"""Rotas de tarefas: convertem HTTP <-> schemas e chamam o `TaskService`."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import get_task_service
from app.core import messages
from app.models.task import TaskStatus
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskReplace,
    TaskResponse,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/tarefas", tags=[messages.TAG_TASKS])

Service = Annotated[TaskService, Depends(get_task_service)]


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary=messages.SUMMARY_CREATE_TASK,
    description=messages.DESCRIPTION_CREATE_TASK,
    response_description=messages.RESPONSE_CREATE_TASK,
)
def create_task(data: TaskCreate, service: Service) -> TaskResponse:
    """Cria uma tarefa."""
    return TaskResponse.model_validate(service.create(data))


@router.get(
    "",
    response_model=TaskListResponse,
    summary=messages.SUMMARY_LIST_TASKS,
    description=messages.DESCRIPTION_LIST_TASKS,
    response_description=messages.RESPONSE_LIST_TASKS,
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
    "/{task_id}",
    response_model=TaskResponse,
    summary=messages.SUMMARY_GET_TASK,
    description=messages.DESCRIPTION_GET_TASK,
    response_description=messages.RESPONSE_GET_TASK,
)
def get_task(task_id: uuid.UUID, service: Service) -> TaskResponse:
    """Consulta uma tarefa pelo id."""
    return TaskResponse.model_validate(service.get(task_id))


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary=messages.SUMMARY_REPLACE_TASK,
    description=messages.DESCRIPTION_REPLACE_TASK,
    response_description=messages.RESPONSE_REPLACE_TASK,
)
def replace_task(
    task_id: uuid.UUID, data: TaskReplace, service: Service
) -> TaskResponse:
    """Substitui uma tarefa (PUT)."""
    return TaskResponse.model_validate(service.replace(task_id, data))


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary=messages.SUMMARY_DELETE_TASK,
    description=messages.DESCRIPTION_DELETE_TASK,
    response_description=messages.RESPONSE_DELETE_TASK,
)
def delete_task(task_id: uuid.UUID, service: Service) -> Response:
    """Exclui uma tarefa."""
    service.delete(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
