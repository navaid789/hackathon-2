from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: int
    action_taken: Optional[str] = None
    task_data: Optional[dict] = None


class ChatSessionResponse(BaseModel):
    id: int
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ChatMessageResponse(BaseModel):
    id: int
    user_id: str
    role: str
    content: str
    session_id: Optional[int] = None
    task_data: Optional[str] = None
    action_taken: Optional[str] = None
    created_at: datetime
