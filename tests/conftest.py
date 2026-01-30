"""Shared pytest fixtures for todo app tests."""

import pytest

from src.todo.models import Task
from src.todo.store import TaskStore
from src.todo.services import TaskService


@pytest.fixture
def empty_store() -> TaskStore:
    """Create an empty TaskStore."""
    return TaskStore()


@pytest.fixture
def store_with_tasks() -> TaskStore:
    """Create a TaskStore with sample tasks."""
    store = TaskStore()
    store.add("Buy groceries", "Milk, eggs, bread")
    store.add("Call mom", "")
    store.add("Complete hackathon", "Phase I todo app")
    return store


@pytest.fixture
def empty_service() -> TaskService:
    """Create a TaskService with empty store."""
    return TaskService()


@pytest.fixture
def service_with_tasks() -> TaskService:
    """Create a TaskService with sample tasks."""
    service = TaskService()
    service.create_task("Buy groceries", "Milk, eggs, bread")
    service.create_task("Call mom")
    service.create_task("Complete hackathon", "Phase I todo app")
    return service


@pytest.fixture
def sample_task(empty_store: TaskStore) -> Task:
    """Create a single sample task."""
    return empty_store.add("Sample task", "Sample description")
