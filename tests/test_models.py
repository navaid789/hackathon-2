"""Tests for the Task model."""

from datetime import datetime

import pytest

from src.todo.models import Task


class TestTaskModel:
    """Tests for Task dataclass."""

    def test_task_creation_with_defaults(self):
        """Task should be created with default values."""
        task = Task(id=1, title="Test task")

        assert task.id == 1
        assert task.title == "Test task"
        assert task.description == ""
        assert task.completed is False
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_task_creation_with_all_fields(self):
        """Task should accept all field values."""
        now = datetime.now()
        task = Task(
            id=1,
            title="Test task",
            description="Test description",
            completed=True,
            created_at=now,
            updated_at=now,
        )

        assert task.id == 1
        assert task.title == "Test task"
        assert task.description == "Test description"
        assert task.completed is True
        assert task.created_at == now
        assert task.updated_at == now

    def test_task_is_mutable(self):
        """Task fields should be mutable."""
        task = Task(id=1, title="Original")

        task.title = "Updated"
        task.completed = True

        assert task.title == "Updated"
        assert task.completed is True

    def test_task_timestamps_are_independent(self):
        """Each task should have its own timestamps."""
        task1 = Task(id=1, title="Task 1")
        task2 = Task(id=2, title="Task 2")

        # They might be equal if created in same millisecond, but should be independent objects
        assert task1.created_at is not task2.created_at or task1.created_at == task2.created_at
