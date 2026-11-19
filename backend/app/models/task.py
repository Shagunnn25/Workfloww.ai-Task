from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    assigned_to: UUID
    due_date: date | None = None


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskOut(BaseModel):
    id: UUID
    company_id: UUID
    title: str
    description: str | None
    status: TaskStatus
    assigned_to: UUID
    assignee_name: str
    created_by: UUID
    due_date: date | None
    created_at: datetime
    updated_at: datetime
