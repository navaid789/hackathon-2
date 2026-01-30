"""Todo Console Application - Phase I.

An in-memory Python console application for managing todo tasks.
"""

from .models import Task
from .exceptions import TaskNotFoundError, ValidationError
from .store import TaskStore
from .services import TaskService
from .cli import TodoCLI, main

__version__ = "1.0.0"
__all__ = [
    "Task",
    "TaskNotFoundError",
    "ValidationError",
    "TaskStore",
    "TaskService",
    "TodoCLI",
    "main",
]
