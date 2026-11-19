from datetime import date
from uuid import UUID

import asyncpg

_SELECT_WITH_ASSIGNEE = """
    select t.id, t.company_id, t.title, t.description, t.status, t.assigned_to,
           u.full_name as assignee_name, t.created_by, t.due_date, t.created_at, t.updated_at
    from public.tasks t
    join public.users u on u.id = t.assigned_to
"""


async def get_task_with_assignee(conn: asyncpg.Connection, task_id: UUID):
    return await conn.fetchrow(f"{_SELECT_WITH_ASSIGNEE} where t.id = $1", task_id)


async def create_task(
    conn: asyncpg.Connection,
    company_id: UUID,
    title: str,
    description: str | None,
    assigned_to: UUID,
    created_by: UUID,
    due_date: date | None,
):
    task_id = await conn.fetchval(
        """
        insert into public.tasks (company_id, title, description, assigned_to, created_by, due_date)
        values ($1, $2, $3, $4, $5, $6)
        returning id
        """,
        company_id,
        title,
        description,
        assigned_to,
        created_by,
        due_date,
    )
    return await get_task_with_assignee(conn, task_id)


async def list_tasks(conn: asyncpg.Connection):
    # No WHERE clause: RLS alone decides which rows come back (all of the
    # caller's company for a manager, only their own assigned tasks for an
    # employee), so there's one place -- the database -- where that rule
    # can be wrong, not two.
    return await conn.fetch(f"{_SELECT_WITH_ASSIGNEE} order by t.created_at desc")


async def update_task_status(conn: asyncpg.Connection, task_id: UUID, new_status: str):
    row = await conn.fetchrow(
        "update public.tasks set status = $1 where id = $2 returning id",
        new_status,
        task_id,
    )
    if row is None:
        return None
    return await get_task_with_assignee(conn, row["id"])
