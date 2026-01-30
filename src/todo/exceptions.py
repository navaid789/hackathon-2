"""Custom exceptions for the todo application."""


class TodoError(Exception):
    """Base exception for todo application errors."""
    pass


class TaskNotFoundError(TodoError):
    """Raised when a task with the given ID does not exist."""

    def __init__(self, task_id: int) -> None:
        self.task_id = task_id
        super().__init__(f"Task {task_id} not found")


class ValidationError(TodoError):
    """Raised when input validation fails."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
