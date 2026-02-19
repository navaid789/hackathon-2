from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class TaskCreatedPayload(BaseModel):
    task_id: int
    user_id: str
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: Optional[datetime] = None
    created_at: datetime


class TaskUpdatedPayload(BaseModel):
    task_id: int
    user_id: str
    changes: Dict[str, Dict[str, Any]]  # {"field": {"old": ..., "new": ...}}
    updated_at: datetime


class TaskCompletedPayload(BaseModel):
    task_id: int
    user_id: str
    completed: bool
    completed_at: datetime
    time_to_complete_hours: Optional[float] = None


class TaskDeletedPayload(BaseModel):
    task_id: int
    user_id: str
    title: str
    deleted_at: datetime
