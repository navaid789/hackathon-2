import json
from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select
from app.models import Task

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task for the user. Supports optional priority and due date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The task title"},
                    "description": {"type": "string", "description": "Optional task description"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "urgent"],
                        "description": "Task priority level (default: medium)",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Optional due date in ISO format (e.g. 2026-02-15 or 2026-02-15T14:00:00Z)",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List all tasks for the user, showing id, title, description, completion status, priority, and due date",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a task as completed (toggle). Use the task id from list_tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "The task ID to complete/uncomplete"},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task permanently. Use the task id from list_tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "The task ID to delete"},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update a task's title, description, priority, or due date. Use the task id from list_tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "The task ID to update"},
                    "title": {"type": "string", "description": "New title"},
                    "description": {"type": "string", "description": "New description"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "urgent"],
                        "description": "New priority",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "New due date in ISO format (e.g. 2026-02-15), or empty string to clear",
                    },
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_tasks",
            "description": "Search tasks by keyword in title or description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keyword to match in title or description"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "filter_tasks",
            "description": "Filter tasks by status, priority, or due date window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["completed", "incomplete", "all"],
                        "description": "Filter by completion status (default: all)",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "urgent"],
                        "description": "Filter by priority level",
                    },
                    "due": {
                        "type": "string",
                        "enum": ["overdue", "today", "this_week"],
                        "description": "Filter by due date window",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_all_tasks",
            "description": "Mark all incomplete tasks as completed.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_completed_tasks",
            "description": "Delete all completed tasks permanently.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


def _parse_due_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # Try ISO format with time
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass
    try:
        # Try date-only format
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def execute_tool(
    tool_name: str, arguments: dict, user_id: str, session: Session
) -> tuple[str, str | None, dict | None]:
    """Execute a tool call and return (result_text, action_taken, task_data)."""
    if not arguments:
        arguments = {}
    # Coerce task_id to int — some LLM providers return it as string
    if "task_id" in arguments:
        try:
            arguments["task_id"] = int(arguments["task_id"])
        except (ValueError, TypeError):
            return json.dumps({"error": "Invalid task_id"}), None, None

    if tool_name == "create_task":
        due = _parse_due_date(arguments.get("due_date"))
        task = Task(
            user_id=user_id,
            title=arguments["title"],
            description=arguments.get("description", ""),
            priority=arguments.get("priority", "medium"),
            due_date=due,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return (
            json.dumps({"success": True, "task_id": task.id, "title": task.title, "priority": task.priority, "due_date": task.due_date.isoformat() if task.due_date else None}),
            "created_task",
            _task_to_dict(task),
        )

    elif tool_name == "list_tasks":
        tasks = session.exec(select(Task).where(Task.user_id == user_id)).all()
        task_list = [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "completed": t.completed,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in tasks
        ]
        return (
            json.dumps({"tasks": task_list, "total": len(task_list)}),
            "listed_tasks",
            None,
        )

    elif tool_name == "complete_task":
        task = session.get(Task, arguments["task_id"])
        if not task or task.user_id != user_id:
            return json.dumps({"error": "Task not found"}), None, None
        task.completed = not task.completed
        task.updated_at = datetime.now(timezone.utc)
        session.add(task)
        session.commit()
        session.refresh(task)
        return (
            json.dumps({"success": True, "task_id": task.id, "completed": task.completed}),
            "completed_task",
            _task_to_dict(task),
        )

    elif tool_name == "delete_task":
        task = session.get(Task, arguments["task_id"])
        if not task or task.user_id != user_id:
            return json.dumps({"error": "Task not found"}), None, None
        task_data = _task_to_dict(task)
        session.delete(task)
        session.commit()
        return (
            json.dumps({"success": True, "deleted_task_id": arguments["task_id"]}),
            "deleted_task",
            task_data,
        )

    elif tool_name == "update_task":
        task = session.get(Task, arguments["task_id"])
        if not task or task.user_id != user_id:
            return json.dumps({"error": "Task not found"}), None, None
        if arguments.get("title") is not None:
            task.title = arguments["title"]
        if arguments.get("description") is not None:
            task.description = arguments["description"]
        if arguments.get("priority") is not None:
            task.priority = arguments["priority"]
        if "due_date" in arguments:
            task.due_date = _parse_due_date(arguments["due_date"])
        task.updated_at = datetime.now(timezone.utc)
        session.add(task)
        session.commit()
        session.refresh(task)
        return (
            json.dumps({"success": True, "task_id": task.id, "title": task.title, "priority": task.priority, "due_date": task.due_date.isoformat() if task.due_date else None}),
            "updated_task",
            _task_to_dict(task),
        )

    elif tool_name == "search_tasks":
        query = arguments["query"].lower()
        tasks = session.exec(select(Task).where(Task.user_id == user_id)).all()
        matches = [
            t for t in tasks
            if query in t.title.lower() or query in (t.description or "").lower()
        ]
        task_list = [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "completed": t.completed,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
            }
            for t in matches
        ]
        return (
            json.dumps({"tasks": task_list, "total": len(task_list), "query": arguments["query"]}),
            "searched_tasks",
            None,
        )

    elif tool_name == "filter_tasks":
        tasks = session.exec(select(Task).where(Task.user_id == user_id)).all()
        filtered = list(tasks)

        status = arguments.get("status", "all")
        if status == "completed":
            filtered = [t for t in filtered if t.completed]
        elif status == "incomplete":
            filtered = [t for t in filtered if not t.completed]

        priority = arguments.get("priority")
        if priority:
            filtered = [t for t in filtered if t.priority == priority]

        due = arguments.get("due")
        if due:
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            week_end = today_start + timedelta(days=7)

            if due == "overdue":
                filtered = [t for t in filtered if t.due_date and t.due_date < now and not t.completed]
            elif due == "today":
                filtered = [t for t in filtered if t.due_date and today_start <= t.due_date < today_end]
            elif due == "this_week":
                filtered = [t for t in filtered if t.due_date and today_start <= t.due_date < week_end]

        task_list = [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "completed": t.completed,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
            }
            for t in filtered
        ]
        return (
            json.dumps({"tasks": task_list, "total": len(task_list), "filters": {k: v for k, v in arguments.items() if v}}),
            "filtered_tasks",
            None,
        )

    elif tool_name == "complete_all_tasks":
        tasks = session.exec(
            select(Task).where(Task.user_id == user_id, Task.completed == False)
        ).all()
        count = len(tasks)
        for t in tasks:
            t.completed = True
            t.updated_at = datetime.now(timezone.utc)
            session.add(t)
        session.commit()
        return (
            json.dumps({"success": True, "completed_count": count}),
            "completed_all_tasks",
            None,
        )

    elif tool_name == "delete_completed_tasks":
        tasks = session.exec(
            select(Task).where(Task.user_id == user_id, Task.completed == True)
        ).all()
        count = len(tasks)
        for t in tasks:
            session.delete(t)
        session.commit()
        return (
            json.dumps({"success": True, "deleted_count": count}),
            "deleted_completed_tasks",
            None,
        )

    return json.dumps({"error": f"Unknown tool: {tool_name}"}), None, None


def _task_to_dict(task: Task) -> dict:
    return {
        "id": task.id,
        "user_id": task.user_id,
        "title": task.title,
        "description": task.description,
        "completed": task.completed,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }
