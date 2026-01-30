# Implementation Plan: Phase I - Todo Console Application

**Branch**: `phase1-console-app` | **Date**: 2026-01-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/phase1-console-app/spec.md`

## Summary

Build an in-memory Python console todo application with CRUD operations. The app provides an interactive command-line interface for managing tasks. Technical approach uses a clean architecture with separate layers for models, services, and CLI.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: None (standard library only: dataclasses, datetime, typing)
**Storage**: In-memory (Python list/dict)
**Testing**: pytest (manual testing for Phase I, automated tests optional)
**Target Platform**: Linux/macOS/Windows console
**Project Type**: Single Python application
**Performance Goals**: Sub-100ms response for all commands
**Constraints**: No external dependencies, in-memory only, no persistence
**Scale/Scope**: Support 1000+ tasks in memory

## Constitution Check

*GATE: Verified against `.specify/memory/constitution.md`*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-Driven Development | PASS | Spec created before implementation |
| II. Minimal Viable Implementation | PASS | Using only standard library |
| III. Clean Code Standards | PENDING | Will enforce during implementation |
| IV. Test-First Approach | OPTIONAL | Manual testing for Phase I MVP |
| V. Modular Architecture | PASS | Separated into models/services/cli |
| VI. User Experience First | PENDING | Clear CLI commands defined |

## Project Structure

### Documentation (this feature)

```text
specs/phase1-console-app/
├── spec.md              # Feature specification (created)
├── plan.md              # This file
└── tasks.md             # To be created by /sp.tasks
```

### Source Code (repository root)

```text
src/
└── todo/
    ├── __init__.py      # Package initialization
    ├── models.py        # Task dataclass
    ├── store.py         # In-memory task storage
    ├── services.py      # Business logic (CRUD operations)
    └── cli.py           # Command-line interface

main.py                  # Entry point
pyproject.toml           # UV project configuration
README.md                # Project documentation
```

**Structure Decision**: Single project structure selected. Clean separation between:
- **models.py**: Pure data structures (Task dataclass)
- **store.py**: In-memory storage abstraction (TaskStore class)
- **services.py**: Business logic layer (TaskService class)
- **cli.py**: User interface layer (command parsing, display formatting)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLI Layer                               │
│  cli.py - Parses commands, formats output, handles user input  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Service Layer                              │
│  services.py - Business logic, validation, CRUD operations     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Store Layer                               │
│  store.py - In-memory storage, ID generation, data access      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Model Layer                               │
│  models.py - Task dataclass with fields and timestamps         │
└─────────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. Task Model (models.py)

```python
@dataclass
class Task:
    id: int
    title: str
    description: str = ""
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
```

### 2. Task Store (store.py)

```python
class TaskStore:
    """In-memory task storage with auto-incrementing IDs."""

    def __init__(self) -> None:
        self._tasks: dict[int, Task] = {}
        self._next_id: int = 1

    def add(self, task: Task) -> Task: ...
    def get(self, task_id: int) -> Task | None: ...
    def get_all(self) -> list[Task]: ...
    def update(self, task: Task) -> Task: ...
    def delete(self, task_id: int) -> bool: ...
```

### 3. Task Service (services.py)

```python
class TaskService:
    """Business logic for task operations."""

    def __init__(self, store: TaskStore) -> None: ...

    def create_task(self, title: str, description: str = "") -> Task: ...
    def list_tasks(self) -> list[Task]: ...
    def get_task(self, task_id: int) -> Task: ...
    def update_task(self, task_id: int, title: str | None, description: str | None) -> Task: ...
    def delete_task(self, task_id: int) -> None: ...
    def complete_task(self, task_id: int) -> Task: ...
    def uncomplete_task(self, task_id: int) -> Task: ...
```

### 4. CLI Interface (cli.py)

```python
class TodoCLI:
    """Command-line interface for todo app."""

    def __init__(self, service: TaskService) -> None: ...

    def run(self) -> None:
        """Main REPL loop."""

    def parse_command(self, line: str) -> tuple[str, list[str]]: ...
    def execute(self, command: str, args: list[str]) -> None: ...

    # Command handlers
    def cmd_add(self, args: list[str]) -> None: ...
    def cmd_list(self, args: list[str]) -> None: ...
    def cmd_view(self, args: list[str]) -> None: ...
    def cmd_update(self, args: list[str]) -> None: ...
    def cmd_delete(self, args: list[str]) -> None: ...
    def cmd_complete(self, args: list[str]) -> None: ...
    def cmd_uncomplete(self, args: list[str]) -> None: ...
    def cmd_help(self, args: list[str]) -> None: ...
```

## Error Handling Strategy

| Error Type | Handling |
|------------|----------|
| Task not found | Raise `TaskNotFoundError`, CLI displays friendly message |
| Empty title | Raise `ValidationError`, CLI displays "Title cannot be empty" |
| Invalid ID format | CLI catches ValueError, displays "Invalid task ID" |
| Unknown command | CLI displays help with available commands |
| Keyboard interrupt (Ctrl+C) | CLI catches, displays "Goodbye!", exits cleanly |

## Implementation Phases

### Phase 1: Foundation
1. Set up UV project structure
2. Create Task model
3. Create TaskStore with in-memory storage

### Phase 2: Business Logic
4. Create TaskService with all CRUD operations
5. Add validation logic
6. Create custom exceptions

### Phase 3: CLI Interface
7. Create command parser
8. Implement all command handlers
9. Add help and exit commands
10. Polish output formatting

### Phase 4: Polish
11. Add error handling
12. Create README with usage instructions
13. Manual testing of all scenarios

## Complexity Tracking

No constitution violations. Simple single-project structure with standard library only.

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Data loss on exit | Documented as Phase I limitation; Phase II adds persistence |
| Complex command parsing | Use shlex for proper quote handling |
| Long title display in list | Truncate to 50 chars in list view, full in detail view |

## Next Steps

1. Run `/sp.tasks` to generate actionable task list
2. Implement tasks in order
3. Manual testing against acceptance scenarios in spec
