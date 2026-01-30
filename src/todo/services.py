"""Business logic layer for todo operations."""

from typing import Optional

from .exceptions import TaskNotFoundError, ValidationError
from .models import Task
from .store import TaskStore


class TaskService:
    """Service class providing business logic for task operations.

    Acts as an intermediary between the CLI and the storage layer,
    handling validation and business rules.
    """

    def __init__(self, store: Optional[TaskStore] = None) -> None:
        """Initialize the service with a task store.

        Args:
            store: Optional TaskStore instance. Creates new one if not provided.
        """
        self._store = store or TaskStore()

    def create_task(self, title: str, description: str = "") -> Task:
        """Create a new task.

        Args:
            title: The task title (required, non-empty).
            description: Optional task description.

        Returns:
            The newly created Task.

        Raises:
            ValidationError: If title is empty or too long.
        """
        if not title or not title.strip():
            raise ValidationError("Task title cannot be empty")

        title = title.strip()
        if len(title) > 200:
            raise ValidationError("Task title cannot exceed 200 characters")

        return self._store.add(title, description.strip() if description else "")

    def list_tasks(self) -> list[Task]:
        """Get all tasks.

        Returns:
            List of all tasks ordered by ID.
        """
        return self._store.get_all()

    def get_task(self, task_id: int) -> Task:
        """Get a specific task by ID.

        Args:
            task_id: The ID of the task to retrieve.

        Returns:
            The Task with the given ID.

        Raises:
            TaskNotFoundError: If no task exists with the given ID.
        """
        task = self._store.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> Task:
        """Update a task's title and/or description.

        Args:
            task_id: The ID of the task to update.
            title: New title (if provided, must be non-empty).
            description: New description (if provided).

        Returns:
            The updated Task.

        Raises:
            TaskNotFoundError: If no task exists with the given ID.
            ValidationError: If title is empty or too long.
        """
        task = self.get_task(task_id)

        if title is not None:
            title = title.strip()
            if not title:
                raise ValidationError("Task title cannot be empty")
            if len(title) > 200:
                raise ValidationError("Task title cannot exceed 200 characters")
            task.title = title

        if description is not None:
            task.description = description.strip()

        return self._store.update(task)

    def delete_task(self, task_id: int) -> None:
        """Delete a task.

        Args:
            task_id: The ID of the task to delete.

        Raises:
            TaskNotFoundError: If no task exists with the given ID.
        """
        if not self._store.delete(task_id):
            raise TaskNotFoundError(task_id)

    def complete_task(self, task_id: int) -> Task:
        """Mark a task as complete.

        Args:
            task_id: The ID of the task to complete.

        Returns:
            The updated Task.

        Raises:
            TaskNotFoundError: If no task exists with the given ID.
        """
        task = self.get_task(task_id)
        if task.completed:
            raise ValidationError(f"Task {task_id} is already complete")
        task.completed = True
        return self._store.update(task)

    def uncomplete_task(self, task_id: int) -> Task:
        """Mark a task as incomplete.

        Args:
            task_id: The ID of the task to mark incomplete.

        Returns:
            The updated Task.

        Raises:
            TaskNotFoundError: If no task exists with the given ID.
        """
        task = self.get_task(task_id)
        if not task.completed:
            raise ValidationError(f"Task {task_id} is already incomplete")
        task.completed = False
        return self._store.update(task)
