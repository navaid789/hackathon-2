import json
from datetime import datetime, timezone
from sqlmodel import Session, select
from app.models import Task

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task for the user",

            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The task title"},
                    "description": {"type": "string", "description": "Optional task description"},
                },
                "required": ["title", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List all tasks for the user, showing their id, title, description, and completion status",

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
            "description": "Update a task's title or description. Use the task id from list_tasks.",

            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "The task ID to update"},
                    "title": {"type": ["string", "null"], "description": "New title (null to keep current)"},
                    "description": {"type": ["string", "null"], "description": "New description (null to keep current)"},
                },
                "required": ["task_id", "title", "description"],
            },
        },
    },
]


def execute_tool(
    tool_name: str, arguments: dict, user_id: str, session: Session
) -> tuple[str, str | None, dict | None]:
    """Execute a tool call and return (result_text, action_taken, task_data)."""

    if tool_name == "create_task":
        task = Task(
            user_id=user_id,
            title=arguments["title"],
            description=arguments.get("description", ""),
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return (
            json.dumps({"success": True, "task_id": task.id, "title": task.title}),
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
        task.updated_at = datetime.now(timezone.utc)
        session.add(task)
        session.commit()
        session.refresh(task)
        return (
            json.dumps({"success": True, "task_id": task.id, "title": task.title}),
            "updated_task",
            _task_to_dict(task),
        )

    return json.dumps({"error": f"Unknown tool: {tool_name}"}), None, None


def _task_to_dict(task: Task) -> dict:
    return {
        "id": task.id,
        "user_id": task.user_id,
        "title": task.title,
        "description": task.description,
        "completed": task.completed,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }
