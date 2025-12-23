from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    pending = "pending"
    completed = "completed"


class TaskBase(BaseModel):
    title: str = Field(..., description="Title of the task", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Optional description of the task")
    status: TaskStatus = Field(TaskStatus.pending, description="Status of the task: pending or completed")

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if v is None or not v.strip():
            raise ValueError("title must be a non-empty string")
        return v.strip()


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Updated title", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Updated description")
    status: Optional[TaskStatus] = Field(None, description="Updated status")

    @field_validator("title")
    @classmethod
    def title_not_empty_if_present(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("title must be a non-empty string when provided")
        return v.strip() if isinstance(v, str) else v


class TaskOut(BaseModel):
    id: int = Field(..., description="Unique identifier")
    title: str = Field(..., description="Title")
    description: Optional[str] = Field(None, description="Description")
    status: TaskStatus = Field(..., description="Status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class PaginatedTasks(BaseModel):
    total: int = Field(..., description="Total number of matching tasks")
    page: int = Field(..., description="Current page, 1-based")
    page_size: int = Field(..., description="Number of items per page")
    items: List[TaskOut] = Field(..., description="Tasks on this page")
