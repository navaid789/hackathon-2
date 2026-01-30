"""Tests for custom exceptions."""

import pytest

from src.todo.exceptions import TaskNotFoundError, ValidationError


class TestTaskNotFoundError:
    """Tests for TaskNotFoundError."""

    def test_error_message_with_task_id(self):
        """Error should include task ID in message."""
        error = TaskNotFoundError(42)

        assert error.task_id == 42
        assert "42" in str(error)
        assert "not found" in str(error).lower()

    def test_error_is_exception(self):
        """TaskNotFoundError should be an Exception."""
        error = TaskNotFoundError(1)

        assert isinstance(error, Exception)

    def test_error_can_be_raised(self):
        """Error should be raiseable and catchable."""
        with pytest.raises(TaskNotFoundError) as exc_info:
            raise TaskNotFoundError(99)

        assert exc_info.value.task_id == 99


class TestValidationError:
    """Tests for ValidationError."""

    def test_error_with_message(self):
        """Error should store and display the message."""
        error = ValidationError("Title cannot be empty")

        assert error.message == "Title cannot be empty"
        assert "Title cannot be empty" in str(error)

    def test_error_is_exception(self):
        """ValidationError should be an Exception."""
        error = ValidationError("test")

        assert isinstance(error, Exception)

    def test_error_can_be_raised(self):
        """Error should be raiseable and catchable."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Invalid input")

        assert exc_info.value.message == "Invalid input"
