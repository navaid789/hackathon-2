"""In-memory task storage for the todo application."""

from datetime import datetime
from typing import Optional

from .models import Task


class TaskStore:
    """In-memory storage for tasks with auto-incrementing IDs.

    Provides basic CRUD operations for Task objects. All data is stored
    in memory and will be lost when the application exits.
    """

    def __init__(self) -> None:
        """Initialize an empty task store."""
        self._tasks: dict[int, Task] = {}
        self._next_id: int = 1

    def add(self, title: str, description: str = "") -> Task:
        """Add a new task to the store.

        Args:
            title: The task title (required).
            description: Optional task description.

        Returns:
            The newly created Task with auto-generated ID.
        """
        task = Task(
            id=self._next_id,
            title=title,
            description=description,
            completed=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self._tasks[task.id] = task
        self._next_id += 1
        return task

    def get(self, task_id: int) -> Optional[Task]:
        """Get a task by its ID.

        Args:
            task_id: The ID of the task to retrieve.

        Returns:
            The Task if found, None otherwise.
        """
        return self._tasks.get(task_id)

    def get_all(self) -> list[Task]:
        """Get all tasks in the store.

        Returns:
            List of all tasks, ordered by ID.
        """
        return sorted(self._tasks.values(), key=lambda t: t.id)

    def update(self, task: Task) -> Task:
        """Update an existing task in the store.

        Args:
            task: The task with updated values.

        Returns:
            The updated task.
        """
        task.updated_at = datetime.now()
        self._tasks[task.id] = task
        return task

    def delete(self, task_id: int) -> bool:
        """Delete a task from the store.

        Args:
            task_id: The ID of the task to delete.

        Returns:
            True if the task was deleted, False if not found.
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def count(self) -> int:
        """Get the number of tasks in the store.

        Returns:
            The total number of tasks.
        """
        return len(self._tasks)
