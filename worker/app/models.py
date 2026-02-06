from datetime import datetime, timezone, date
from typing import Optional
from sqlmodel import SQLModel, Field


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    notification_type: str  # "overdue_alert", "daily_summary"
    title: str
    content: str  # May be JSON for summaries
    related_task_id: Optional[int] = Field(default=None)
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AnalyticsBucket(SQLModel, table=True):
    __tablename__ = "analytics_buckets"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    bucket_date: date
    tasks_created: int = Field(default=0)
    tasks_completed: int = Field(default=0)
    tasks_deleted: int = Field(default=0)
    total_completion_time_hours: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        # Unique constraint on (user_id, bucket_date)
        pass


class ProcessedEvent(SQLModel, table=True):
    __tablename__ = "processed_events"

    event_id: str = Field(primary_key=True)
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
