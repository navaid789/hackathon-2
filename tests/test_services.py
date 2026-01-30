"""Tests for TaskService."""

import pytest

from src.todo.exceptions import TaskNotFoundError, ValidationError
from src.todo.models import Task
from src.todo.services import TaskService


class TestTaskServiceCreateTask:
    """Tests for TaskService.create_task()."""

    def test_create_task_with_title_only(self, empty_service: TaskService):
        """Should create task with just a title."""
        task = empty_service.create_task("Buy groceries")

        assert task.id == 1
        assert task.title == "Buy groceries"
        assert task.description == ""
        assert task.completed is False

    def test_create_task_with_title_and_description(self, empty_service: TaskService):
        """Should create task with title and description."""
        task = empty_service.create_task("Buy groceries", "Milk, eggs, bread")

        assert task.title == "Buy groceries"
        assert task.description == "Milk, eggs, bread"

    def test_create_task_strips_whitespace(self, empty_service: TaskService):
        """Should strip whitespace from title and description."""
        task = empty_service.create_task("  Buy groceries  ", "  Milk, eggs  ")

        assert task.title == "Buy groceries"
        assert task.description == "Milk, eggs"

    def test_create_task_empty_title_raises_error(self, empty_service: TaskService):
        """Should raise ValidationError for empty title."""
        with pytest.raises(ValidationError) as exc_info:
            empty_service.create_task("")

        assert "empty" in exc_info.value.message.lower()

    def test_create_task_whitespace_title_raises_error(self, empty_service: TaskService):
        """Should raise ValidationError for whitespace-only title."""
        with pytest.raises(ValidationError) as exc_info:
            empty_service.create_task("   ")

        assert "empty" in exc_info.value.message.lower()

    def test_create_task_long_title_raises_error(self, empty_service: TaskService):
        """Should raise ValidationError for title over 200 chars."""
        long_title = "x" * 201

        with pytest.raises(ValidationError) as exc_info:
            empty_service.create_task(long_title)

        assert "200" in exc_info.value.message


class TestTaskServiceListTasks:
    """Tests for TaskService.list_tasks()."""

    def test_list_empty(self, empty_service: TaskService):
        """Should return empty list when no tasks."""
        tasks = empty_service.list_tasks()

        assert tasks == []

    def test_list_with_tasks(self, service_with_tasks: TaskService):
        """Should return all tasks."""
        tasks = service_with_tasks.list_tasks()

        assert len(tasks) == 3

    def test_list_returns_tasks_in_order(self, service_with_tasks: TaskService):
        """Should return tasks ordered by ID."""
        tasks = service_with_tasks.list_tasks()

        assert tasks[0].id < tasks[1].id < tasks[2].id


class TestTaskServiceGetTask:
    """Tests for TaskService.get_task()."""

    def test_get_existing_task(self, service_with_tasks: TaskService):
        """Should return task when it exists."""
        task = service_with_tasks.get_task(1)

        assert task.id == 1
        assert task.title == "Buy groceries"

    def test_get_nonexistent_task_raises_error(self, empty_service: TaskService):
        """Should raise TaskNotFoundError for nonexistent task."""
        with pytest.raises(TaskNotFoundError) as exc_info:
            empty_service.get_task(999)

        assert exc_info.value.task_id == 999


class TestTaskServiceUpdateTask:
    """Tests for TaskService.update_task()."""

    def test_update_title(self, service_with_tasks: TaskService):
        """Should update task title."""
        task = service_with_tasks.update_task(1, title="New groceries list")

        assert task.title == "New groceries list"

    def test_update_description(self, service_with_tasks: TaskService):
        """Should update task description."""
        task = service_with_tasks.update_task(1, description="New description")

        assert task.description == "New description"

    def test_update_both_fields(self, service_with_tasks: TaskService):
        """Should update both title and description."""
        task = service_with_tasks.update_task(
            1,
            title="New title",
            description="New description"
        )

        assert task.title == "New title"
        assert task.description == "New description"

    def test_update_strips_whitespace(self, service_with_tasks: TaskService):
        """Should strip whitespace from updated values."""
        task = service_with_tasks.update_task(1, title="  Stripped  ")

        assert task.title == "Stripped"

    def test_update_nonexistent_task_raises_error(self, empty_service: TaskService):
        """Should raise TaskNotFoundError for nonexistent task."""
        with pytest.raises(TaskNotFoundError):
            empty_service.update_task(999, title="Test")

    def test_update_empty_title_raises_error(self, service_with_tasks: TaskService):
        """Should raise ValidationError for empty title."""
        with pytest.raises(ValidationError) as exc_info:
            service_with_tasks.update_task(1, title="")

        assert "empty" in exc_info.value.message.lower()

    def test_update_long_title_raises_error(self, service_with_tasks: TaskService):
        """Should raise ValidationError for title over 200 chars."""
        with pytest.raises(ValidationError):
            service_with_tasks.update_task(1, title="x" * 201)


class TestTaskServiceDeleteTask:
    """Tests for TaskService.delete_task()."""

    def test_delete_existing_task(self, service_with_tasks: TaskService):
        """Should delete task without error."""
        service_with_tasks.delete_task(1)

        with pytest.raises(TaskNotFoundError):
            service_with_tasks.get_task(1)

    def test_delete_nonexistent_task_raises_error(self, empty_service: TaskService):
        """Should raise TaskNotFoundError for nonexistent task."""
        with pytest.raises(TaskNotFoundError) as exc_info:
            empty_service.delete_task(999)

        assert exc_info.value.task_id == 999


class TestTaskServiceCompleteTask:
    """Tests for TaskService.complete_task()."""

    def test_complete_task(self, service_with_tasks: TaskService):
        """Should mark task as complete."""
        task = service_with_tasks.complete_task(1)

        assert task.completed is True

    def test_complete_already_completed_raises_error(self, service_with_tasks: TaskService):
        """Should raise ValidationError if already complete."""
        service_with_tasks.complete_task(1)

        with pytest.raises(ValidationError) as exc_info:
            service_with_tasks.complete_task(1)

        assert "already complete" in exc_info.value.message.lower()

    def test_complete_nonexistent_task_raises_error(self, empty_service: TaskService):
        """Should raise TaskNotFoundError for nonexistent task."""
        with pytest.raises(TaskNotFoundError):
            empty_service.complete_task(999)


class TestTaskServiceUncompleteTask:
    """Tests for TaskService.uncomplete_task()."""

    def test_uncomplete_task(self, service_with_tasks: TaskService):
        """Should mark task as incomplete."""
        service_with_tasks.complete_task(1)
        task = service_with_tasks.uncomplete_task(1)

        assert task.completed is False

    def test_uncomplete_already_incomplete_raises_error(self, service_with_tasks: TaskService):
        """Should raise ValidationError if already incomplete."""
        with pytest.raises(ValidationError) as exc_info:
            service_with_tasks.uncomplete_task(1)

        assert "already incomplete" in exc_info.value.message.lower()

    def test_uncomplete_nonexistent_task_raises_error(self, empty_service: TaskService):
        """Should raise TaskNotFoundError for nonexistent task."""
        with pytest.raises(TaskNotFoundError):
            empty_service.uncomplete_task(999)


class TestTaskServiceIntegration:
    """Integration tests for TaskService."""

    def test_full_task_lifecycle(self, empty_service: TaskService):
        """Test complete task lifecycle: create -> update -> complete -> delete."""
        # Create
        task = empty_service.create_task("Original title", "Original description")
        assert task.id == 1

        # Update
        task = empty_service.update_task(1, title="Updated title")
        assert task.title == "Updated title"

        # Complete
        task = empty_service.complete_task(1)
        assert task.completed is True

        # Uncomplete
        task = empty_service.uncomplete_task(1)
        assert task.completed is False

        # Delete
        empty_service.delete_task(1)
        with pytest.raises(TaskNotFoundError):
            empty_service.get_task(1)

    def test_multiple_tasks_independent(self, empty_service: TaskService):
        """Operations on one task should not affect others."""
        task1 = empty_service.create_task("Task 1")
        task2 = empty_service.create_task("Task 2")
        task3 = empty_service.create_task("Task 3")

        # Complete task 2
        empty_service.complete_task(2)

        # Delete task 1
        empty_service.delete_task(1)

        # Verify task 3 unaffected
        task3_check = empty_service.get_task(3)
        assert task3_check.completed is False
        assert task3_check.title == "Task 3"

        # Verify correct number of tasks
        assert len(empty_service.list_tasks()) == 2
