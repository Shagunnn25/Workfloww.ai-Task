from fastapi import APIRouter, Depends

from app.core.deps import RequestContext, get_request_context
from app.models.user import EmployeeOut
from app.services import employee_service

router = APIRouter()


@router.get("/employees", response_model=list[EmployeeOut])
async def list_employees(ctx: RequestContext = Depends(get_request_context)) -> list[EmployeeOut]:
    return await employee_service.list_employees(ctx.conn, ctx.caller)
