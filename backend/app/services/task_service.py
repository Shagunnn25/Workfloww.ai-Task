from uuid import UUID

import asyncpg
from fastapi import HTTPException, status

from app.core.deps import Caller
from app.models.task import TaskCreate, TaskOut
from app.repositories import tasks_repo, users_repo


def _to_task_out(row) -> TaskOut:
    return TaskOut(**dict(row))


async def create_task(conn: asyncpg.Connection, caller: Caller, payload: TaskCreate) -> TaskOut:
    if caller.role != "manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can create tasks")

    assignee = await users_repo.get_user_by_id_and_company(conn, payload.assigned_to, caller.company_id)
    if assignee is None or assignee["role"] != "employee":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="assigned_to must be an employee in your company",
        )

    row = await tasks_repo.create_task(
        conn,
        company_id=caller.company_id,
        title=payload.title,
        description=payload.description,
        assigned_to=payload.assigned_to,
        created_by=caller.id,
        due_date=payload.due_date,
    )
    return _to_task_out(row)


async def list_tasks(conn: asyncpg.Connection) -> list[TaskOut]:
    rows = await tasks_repo.list_tasks(conn)
    return [_to_task_out(r) for r in rows]


async def update_task_status(conn: asyncpg.Connection, task_id: UUID, new_status: str) -> TaskOut:
    row = await tasks_repo.update_task_status(conn, task_id, new_status)
    if row is None:
        # Covers "doesn't exist" and "exists but RLS hid it" (wrong company,
        # or an employee touching a task that isn't theirs) with the same
        # 404 -- so a caller probing task ids can't tell those cases apart.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return _to_task_out(row)
