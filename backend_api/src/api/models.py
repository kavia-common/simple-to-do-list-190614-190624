from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import BigInteger, Column, DateTime, Enum, String, Text
from .database import Base


class TaskStatus(str, PyEnum):
    PENDING = "pending"
    COMPLETED = "completed"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus, name="task_status"), nullable=False, default=TaskStatus.PENDING)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        """Update the updated_at timestamp to now (UTC)."""
        self.updated_at = datetime.now(timezone.utc)
