from uuid import UUID

from pydantic import BaseModel


class EmployeeOut(BaseModel):
    id: UUID
    full_name: str
    email: str
