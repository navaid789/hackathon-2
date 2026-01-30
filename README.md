# Todo Console Application - Phase I

An in-memory Python console application for managing todo tasks. Built using Spec-Driven Development with Claude Code and Spec-Kit Plus.

## Features

- **Add Task** - Create new tasks with title and optional description
- **List Tasks** - View all tasks with status indicators
- **View Task** - See full details of a specific task
- **Update Task** - Modify task title or description
- **Delete Task** - Remove tasks from the list
- **Complete/Uncomplete** - Toggle task completion status

## Requirements

- Python 3.12+
- UV (package manager)

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd hackathon-2
```

### 2. Create virtual environment and install dependencies

```bash
# Using UV
uv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using pip
python -m venv venv
source venv/bin/activate
pip install -e .
```

### 3. Run the application

```bash
# Option 1: Run directly
python main.py

# Option 2: If installed with pip install -e .
todo
```

## Usage

The application provides an interactive command-line interface:

```
==================================================
  Todo Console Application - Phase I
==================================================
Type 'help' for available commands.

todo>
```

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `add <title> [description]` | Create a new task | `add "Buy groceries" "Milk, eggs, bread"` |
| `list` | Show all tasks | `list` |
| `view <id>` | Show task details | `view 1` |
| `update <id> <field> <value>` | Update task | `update 1 title "New title"` |
| `delete <id>` | Remove a task | `delete 1` |
| `complete <id>` | Mark task as done | `complete 1` |
| `uncomplete <id>` | Mark task as pending | `uncomplete 1` |
| `help` | Show help message | `help` |
| `exit` / `quit` | Exit the app | `exit` |

### Command Shortcuts

- `ls` = `list`
- `rm` = `delete`
- `done` = `complete`
- `undo` = `uncomplete`
- `q` = `quit`

### Example Session

```
todo> add "Complete hackathon Phase I"
Created task #1: Complete hackathon Phase I

todo> add "Write documentation" "Create README with usage examples"
Created task #2: Write documentation

todo> list

ID   Status   Title
--------------------------------------------------------------
1    [ ]      Complete hackathon Phase I
2    [ ]      Write documentation
--------------------------------------------------------------
Total: 2 tasks (0 completed, 2 pending)

todo> complete 1
Completed task #1: Complete hackathon Phase I

todo> view 1

========================================
Task #1
========================================
Title:       Complete hackathon Phase I
Description: (none)
Status:      Completed
Created:     2026-01-24 12:00:00
Updated:     2026-01-24 12:01:00
========================================

todo> exit
Goodbye!
```

## Project Structure

```
hackathon-2/
├── src/
│   └── todo/
│       ├── __init__.py     # Package initialization
│       ├── models.py       # Task dataclass
│       ├── exceptions.py   # Custom exceptions
│       ├── store.py        # In-memory storage
│       ├── services.py     # Business logic
│       └── cli.py          # Command-line interface
├── tests/
│   ├── conftest.py         # Shared fixtures
│   ├── test_models.py      # Task model tests
│   ├── test_exceptions.py  # Exception tests
│   ├── test_store.py       # TaskStore tests
│   └── test_services.py    # TaskService tests
├── specs/
│   └── phase1-console-app/
│       ├── spec.md         # Feature specification
│       ├── plan.md         # Implementation plan
│       └── tasks.md        # Task breakdown
├── .specify/
│   └── memory/
│       └── constitution.md # Project principles
├── main.py                 # Entry point
├── pyproject.toml          # UV project config
├── CLAUDE.md               # Claude Code instructions
└── README.md               # This file
```

## Testing

### Install test dependencies

```bash
pip install -e ".[dev]"
```

### Run tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src/todo --cov-report=term-missing

# Run specific test file
pytest tests/test_services.py
```

### Test Coverage

| Module | Coverage |
|--------|----------|
| `services.py` | 100% |
| `store.py` | 97% |
| `exceptions.py` | 100% |
| `models.py` | 81% |

56 tests covering all CRUD operations and edge cases.

## Development Approach

This project was built using **Spec-Driven Development (SDD)**:

1. **Constitution** - Defined project principles and standards
2. **Specification** - Documented user stories and acceptance criteria
3. **Plan** - Designed technical architecture and components
4. **Tasks** - Broke down implementation into actionable items
5. **Implementation** - Generated code via Claude Code

All specifications are available in the `specs/phase1-console-app/` directory.

## Limitations (Phase I)

- **No persistence** - All data is stored in memory and lost on exit
- **Single user** - No authentication or multi-user support
- **Basic features only** - Advanced features (priorities, tags, due dates) planned for later phases

## Next Phases

- **Phase II** - Full-stack web application with Next.js, FastAPI, and Neon DB
- **Phase III** - AI chatbot with natural language interface
- **Phase IV** - Kubernetes deployment
- **Phase V** - Advanced cloud deployment with Kafka and Dapr

## License

MIT License
