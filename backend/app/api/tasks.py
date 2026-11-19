from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.deps import RequestContext, get_request_context
from app.models.task import TaskCreate, TaskOut, TaskStatusUpdate
from app.services import task_service

router = APIRouter()


@router.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, ctx: RequestContext = Depends(get_request_context)) -> TaskOut:
    return await task_service.create_task(ctx.conn, ctx.caller, payload)


@router.get("/tasks", response_model=list[TaskOut])
async def list_tasks(ctx: RequestContext = Depends(get_request_context)) -> list[TaskOut]:
    return await task_service.list_tasks(ctx.conn)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
async def update_task_status(
    task_id: UUID,
    payload: TaskStatusUpdate,
    ctx: RequestContext = Depends(get_request_context),
) -> TaskOut:
    return await task_service.update_task_status(ctx.conn, task_id, payload.status.value)
