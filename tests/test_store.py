"""Tests for TaskStore."""

import pytest

from src.todo.models import Task
from src.todo.store import TaskStore


class TestTaskStoreAdd:
    """Tests for TaskStore.add()."""

    def test_add_returns_task(self, empty_store: TaskStore):
        """Adding a task should return a Task object."""
        task = empty_store.add("Test task", "Description")

        assert isinstance(task, Task)
        assert task.title == "Test task"
        assert task.description == "Description"

    def test_add_assigns_sequential_ids(self, empty_store: TaskStore):
        """Tasks should get sequential IDs starting from 1."""
        task1 = empty_store.add("Task 1", "")
        task2 = empty_store.add("Task 2", "")
        task3 = empty_store.add("Task 3", "")

        assert task1.id == 1
        assert task2.id == 2
        assert task3.id == 3

    def test_add_sets_completed_to_false(self, empty_store: TaskStore):
        """New tasks should be incomplete by default."""
        task = empty_store.add("Test", "")

        assert task.completed is False

    def test_add_sets_timestamps(self, empty_store: TaskStore):
        """New tasks should have created_at and updated_at set."""
        task = empty_store.add("Test", "")

        assert task.created_at is not None
        assert task.updated_at is not None


class TestTaskStoreGet:
    """Tests for TaskStore.get()."""

    def test_get_existing_task(self, store_with_tasks: TaskStore):
        """Should return task when it exists."""
        task = store_with_tasks.get(1)

        assert task is not None
        assert task.id == 1
        assert task.title == "Buy groceries"

    def test_get_nonexistent_task(self, empty_store: TaskStore):
        """Should return None for nonexistent task."""
        task = empty_store.get(999)

        assert task is None

    def test_get_after_delete(self, store_with_tasks: TaskStore):
        """Should return None after task is deleted."""
        store_with_tasks.delete(1)
        task = store_with_tasks.get(1)

        assert task is None


class TestTaskStoreGetAll:
    """Tests for TaskStore.get_all()."""

    def test_get_all_empty_store(self, empty_store: TaskStore):
        """Should return empty list for empty store."""
        tasks = empty_store.get_all()

        assert tasks == []

    def test_get_all_with_tasks(self, store_with_tasks: TaskStore):
        """Should return all tasks."""
        tasks = store_with_tasks.get_all()

        assert len(tasks) == 3

    def test_get_all_returns_copies(self, store_with_tasks: TaskStore):
        """Modifying returned list should not affect store."""
        tasks = store_with_tasks.get_all()
        tasks.clear()

        assert len(store_with_tasks.get_all()) == 3

    def test_get_all_ordered_by_id(self, store_with_tasks: TaskStore):
        """Tasks should be ordered by ID."""
        tasks = store_with_tasks.get_all()

        assert tasks[0].id < tasks[1].id < tasks[2].id


class TestTaskStoreUpdate:
    """Tests for TaskStore.update()."""

    def test_update_modifies_task(self, store_with_tasks: TaskStore):
        """Should update task in store."""
        task = store_with_tasks.get(1)
        task.title = "Updated title"
        task.completed = True

        updated = store_with_tasks.update(task)

        assert updated.title == "Updated title"
        assert updated.completed is True

    def test_update_returns_task(self, store_with_tasks: TaskStore):
        """Should return the updated task."""
        task = store_with_tasks.get(1)
        task.title = "New title"

        result = store_with_tasks.update(task)

        assert isinstance(result, Task)
        assert result.id == task.id

    def test_update_updates_timestamp(self, store_with_tasks: TaskStore):
        """Should update the updated_at timestamp."""
        task = store_with_tasks.get(1)
        original_updated = task.updated_at

        task.title = "Changed"
        store_with_tasks.update(task)

        # Timestamp should be same or later
        assert task.updated_at >= original_updated


class TestTaskStoreDelete:
    """Tests for TaskStore.delete()."""

    def test_delete_existing_task(self, store_with_tasks: TaskStore):
        """Should return True when deleting existing task."""
        result = store_with_tasks.delete(1)

        assert result is True
        assert store_with_tasks.get(1) is None

    def test_delete_nonexistent_task(self, empty_store: TaskStore):
        """Should return False when deleting nonexistent task."""
        result = empty_store.delete(999)

        assert result is False

    def test_delete_reduces_count(self, store_with_tasks: TaskStore):
        """Deleting should reduce task count."""
        initial_count = len(store_with_tasks.get_all())

        store_with_tasks.delete(1)

        assert len(store_with_tasks.get_all()) == initial_count - 1

    def test_delete_does_not_affect_other_ids(self, store_with_tasks: TaskStore):
        """Deleting task should not affect other task IDs."""
        store_with_tasks.delete(2)

        assert store_with_tasks.get(1) is not None
        assert store_with_tasks.get(3) is not None
