"""Task model for the todo application."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Task:
    """Represents a todo task item.

    Attributes:
        id: Unique identifier for the task (auto-generated).
        title: The task title (required, max 200 characters).
        description: Optional detailed description.
        completed: Whether the task is marked as done.
        created_at: Timestamp when task was created.
        updated_at: Timestamp when task was last modified.
    """
    id: int
    title: str
    description: str = ""
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validate task data after initialization."""
        if not self.title or not self.title.strip():
            raise ValueError("Task title cannot be empty")
        if len(self.title) > 200:
            raise ValueError("Task title cannot exceed 200 characters")
        self.title = self.title.strip()
        self.description = self.description.strip() if self.description else ""
