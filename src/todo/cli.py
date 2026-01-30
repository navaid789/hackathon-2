"""Command-line interface for the todo application."""

import shlex
import sys
from typing import Optional

from .exceptions import TaskNotFoundError, ValidationError
from .models import Task
from .services import TaskService


class TodoCLI:
    """Interactive command-line interface for managing tasks.

    Provides a REPL (Read-Eval-Print Loop) for executing todo commands.
    """

    COMMANDS = {
        "add": "add <title> [description] - Create a new task",
        "list": "list - Show all tasks",
        "view": "view <id> - Show task details",
        "update": "update <id> <field> <value> - Update task (field: title or description)",
        "delete": "delete <id> - Remove a task",
        "complete": "complete <id> - Mark task as done",
        "uncomplete": "uncomplete <id> - Mark task as pending",
        "help": "help - Show this help message",
        "exit": "exit/quit - Exit the application",
    }

    def __init__(self, service: Optional[TaskService] = None) -> None:
        """Initialize the CLI with a task service.

        Args:
            service: Optional TaskService instance. Creates new one if not provided.
        """
        self._service = service or TaskService()

    def run(self) -> None:
        """Start the interactive command loop."""
        self._print_welcome()

        while True:
            try:
                line = input("\ntodo> ").strip()
                if not line:
                    continue

                command, args = self._parse_command(line)
                self._execute(command, args)

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except EOFError:
                print("\nGoodbye!")
                break

    def _print_welcome(self) -> None:
        """Print the welcome message."""
        print("=" * 50)
        print("  Todo Console Application - Phase I")
        print("=" * 50)
        print("Type 'help' for available commands.")

    def _parse_command(self, line: str) -> tuple[str, list[str]]:
        """Parse a command line into command and arguments.

        Args:
            line: The raw input line.

        Returns:
            Tuple of (command, list of arguments).
        """
        try:
            parts = shlex.split(line)
        except ValueError:
            # Handle unclosed quotes
            parts = line.split()

        if not parts:
            return "", []

        return parts[0].lower(), parts[1:]

    def _execute(self, command: str, args: list[str]) -> None:
        """Execute a command with the given arguments.

        Args:
            command: The command name.
            args: List of command arguments.
        """
        handlers = {
            "add": self._cmd_add,
            "list": self._cmd_list,
            "ls": self._cmd_list,
            "view": self._cmd_view,
            "update": self._cmd_update,
            "delete": self._cmd_delete,
            "rm": self._cmd_delete,
            "complete": self._cmd_complete,
            "done": self._cmd_complete,
            "uncomplete": self._cmd_uncomplete,
            "undo": self._cmd_uncomplete,
            "help": self._cmd_help,
            "?": self._cmd_help,
            "exit": self._cmd_exit,
            "quit": self._cmd_exit,
            "q": self._cmd_exit,
        }

        handler = handlers.get(command)
        if handler:
            handler(args)
        else:
            print(f"Unknown command: '{command}'")
            print("Type 'help' for available commands.")

    def _cmd_add(self, args: list[str]) -> None:
        """Handle the add command."""
        if not args:
            print("Usage: add <title> [description]")
            print("Example: add \"Buy groceries\" \"Milk, eggs, bread\"")
            return

        title = args[0]
        description = args[1] if len(args) > 1 else ""

        try:
            task = self._service.create_task(title, description)
            print(f"Created task #{task.id}: {task.title}")
        except ValidationError as e:
            print(f"Error: {e.message}")

    def _cmd_list(self, args: list[str]) -> None:
        """Handle the list command."""
        tasks = self._service.list_tasks()

        if not tasks:
            print("No tasks found. Add a task with: add <title>")
            return

        print(f"\n{'ID':<4} {'Status':<8} {'Title':<50}")
        print("-" * 62)

        for task in tasks:
            status = "[x]" if task.completed else "[ ]"
            title = task.title[:47] + "..." if len(task.title) > 50 else task.title
            print(f"{task.id:<4} {status:<8} {title:<50}")

        completed = sum(1 for t in tasks if t.completed)
        print("-" * 62)
        print(f"Total: {len(tasks)} tasks ({completed} completed, {len(tasks) - completed} pending)")

    def _cmd_view(self, args: list[str]) -> None:
        """Handle the view command."""
        if not args:
            print("Usage: view <id>")
            return

        try:
            task_id = int(args[0])
        except ValueError:
            print("Error: Invalid task ID. Must be a number.")
            return

        try:
            task = self._service.get_task(task_id)
            self._print_task_details(task)
        except TaskNotFoundError as e:
            print(f"Error: {e}")

    def _print_task_details(self, task: Task) -> None:
        """Print detailed information about a task."""
        status = "Completed" if task.completed else "Pending"
        print(f"\n{'='*40}")
        print(f"Task #{task.id}")
        print(f"{'='*40}")
        print(f"Title:       {task.title}")
        print(f"Description: {task.description or '(none)'}")
        print(f"Status:      {status}")
        print(f"Created:     {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Updated:     {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*40}")

    def _cmd_update(self, args: list[str]) -> None:
        """Handle the update command."""
        if len(args) < 3:
            print("Usage: update <id> <field> <value>")
            print("Fields: title, description")
            print("Example: update 1 title \"New title\"")
            return

        try:
            task_id = int(args[0])
        except ValueError:
            print("Error: Invalid task ID. Must be a number.")
            return

        field = args[1].lower()
        value = args[2]

        if field not in ("title", "description"):
            print(f"Error: Unknown field '{field}'. Use 'title' or 'description'.")
            return

        try:
            if field == "title":
                task = self._service.update_task(task_id, title=value)
            else:
                task = self._service.update_task(task_id, description=value)
            print(f"Updated task #{task.id}: {task.title}")
        except TaskNotFoundError as e:
            print(f"Error: {e}")
        except ValidationError as e:
            print(f"Error: {e.message}")

    def _cmd_delete(self, args: list[str]) -> None:
        """Handle the delete command."""
        if not args:
            print("Usage: delete <id>")
            return

        try:
            task_id = int(args[0])
        except ValueError:
            print("Error: Invalid task ID. Must be a number.")
            return

        try:
            # Get task first to show title in confirmation
            task = self._service.get_task(task_id)
            title = task.title
            self._service.delete_task(task_id)
            print(f"Deleted task #{task_id}: {title}")
        except TaskNotFoundError as e:
            print(f"Error: {e}")

    def _cmd_complete(self, args: list[str]) -> None:
        """Handle the complete command."""
        if not args:
            print("Usage: complete <id>")
            return

        try:
            task_id = int(args[0])
        except ValueError:
            print("Error: Invalid task ID. Must be a number.")
            return

        try:
            task = self._service.complete_task(task_id)
            print(f"Completed task #{task.id}: {task.title}")
        except TaskNotFoundError as e:
            print(f"Error: {e}")
        except ValidationError as e:
            print(f"Note: {e.message}")

    def _cmd_uncomplete(self, args: list[str]) -> None:
        """Handle the uncomplete command."""
        if not args:
            print("Usage: uncomplete <id>")
            return

        try:
            task_id = int(args[0])
        except ValueError:
            print("Error: Invalid task ID. Must be a number.")
            return

        try:
            task = self._service.uncomplete_task(task_id)
            print(f"Marked task #{task.id} as pending: {task.title}")
        except TaskNotFoundError as e:
            print(f"Error: {e}")
        except ValidationError as e:
            print(f"Note: {e.message}")

    def _cmd_help(self, args: list[str]) -> None:
        """Handle the help command."""
        print("\nAvailable Commands:")
        print("-" * 60)
        for cmd, desc in self.COMMANDS.items():
            print(f"  {desc}")
        print("-" * 60)
        print("\nTips:")
        print("  - Use quotes for titles with spaces: add \"Buy groceries\"")
        print("  - Shortcuts: ls=list, rm=delete, done=complete, q=quit")

    def _cmd_exit(self, args: list[str]) -> None:
        """Handle the exit command."""
        print("Goodbye!")
        sys.exit(0)


def main() -> None:
    """Entry point for the todo CLI application."""
    cli = TodoCLI()
    cli.run()


if __name__ == "__main__":
    main()
