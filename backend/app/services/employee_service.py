import asyncpg
from fastapi import HTTPException, status

from app.core.deps import Caller
from app.models.user import EmployeeOut
from app.repositories import users_repo


async def list_employees(conn: asyncpg.Connection, caller: Caller) -> list[EmployeeOut]:
    if caller.role != "manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can list employees")

    rows = await users_repo.list_employees(conn, caller.company_id)
    return [EmployeeOut(**dict(r)) for r in rows]
