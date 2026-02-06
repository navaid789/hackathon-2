from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate
from app.auth import verify_token, get_user_id
from app.events import publish_event

router = APIRouter(prefix="/api")


def _require_owner(token_payload: dict, url_user_id: str) -> str:
    user_id = get_user_id(token_payload)
    if user_id != url_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user_id


@router.get("/{user_id}/tasks")
def list_tasks(
    user_id: str,
    session: Session = Depends(get_session),
    token: dict = Depends(verify_token),
):
    _require_owner(token, user_id)
    tasks = session.exec(select(Task).where(Task.user_id == user_id)).all()
    return tasks


@router.post("/{user_id}/tasks", status_code=201)
def create_task(
    user_id: str,
    body: TaskCreate,
    session: Session = Depends(get_session),
    token: dict = Depends(verify_token),
):
    _require_owner(token, user_id)
    task = Task(
        user_id=user_id,
        title=body.title,
        description=body.description,
        priority=body.priority,
        due_date=body.due_date,
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Publish task.created event
    publish_event(
        event_type="task.created",
        data={
            "task_id": task.id,
            "user_id": task.user_id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "created_at": task.created_at.isoformat(),
        },
        user_id=user_id,
        task_id=task.id,
    )

    return task


@router.get("/{user_id}/tasks/{task_id}")
def get_task(
    user_id: str,
    task_id: int,
    session: Session = Depends(get_session),
    token: dict = Depends(verify_token),
):
    _require_owner(token, user_id)
    task = session.get(Task, task_id)
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{user_id}/tasks/{task_id}")
def update_task(
    user_id: str,
    task_id: int,
    body: TaskUpdate,
    session: Session = Depends(get_session),
    token: dict = Depends(verify_token),
):
    _require_owner(token, user_id)
    task = session.get(Task, task_id)
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")

    # Track changes for event
    changes = {}
    update_data = body.model_dump(exclude_unset=True)
    for key, new_value in update_data.items():
        old_value = getattr(task, key)
        if old_value != new_value:
            # Serialize datetime for JSON
            if hasattr(old_value, "isoformat"):
                old_value = old_value.isoformat()
            if hasattr(new_value, "isoformat"):
                new_value = new_value.isoformat()
            changes[key] = {"old": old_value, "new": new_value}
        setattr(task, key, body.model_dump(exclude_unset=True)[key])

    task.updated_at = datetime.now(timezone.utc)
    session.add(task)
    session.commit()
    session.refresh(task)

    # Publish task.updated event if there were changes
    if changes:
        publish_event(
            event_type="task.updated",
            data={
                "task_id": task.id,
                "user_id": task.user_id,
                "changes": changes,
                "updated_at": task.updated_at.isoformat(),
            },
            user_id=user_id,
            task_id=task.id,
        )

    return task


@router.delete("/{user_id}/tasks/{task_id}", status_code=204)
def delete_task(
    user_id: str,
    task_id: int,
    session: Session = Depends(get_session),
    token: dict = Depends(verify_token),
):
    _require_owner(token, user_id)
    task = session.get(Task, task_id)
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")

    # Capture task data before deletion for event
    task_title = task.title
    deleted_task_id = task.id

    session.delete(task)
    session.commit()

    # Publish task.deleted event
    publish_event(
        event_type="task.deleted",
        data={
            "task_id": deleted_task_id,
            "user_id": user_id,
            "title": task_title,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
        },
        user_id=user_id,
        task_id=deleted_task_id,
    )


@router.patch("/{user_id}/tasks/{task_id}/complete")
def toggle_complete(
    user_id: str,
    task_id: int,
    session: Session = Depends(get_session),
    token: dict = Depends(verify_token),
):
    _require_owner(token, user_id)
    task = session.get(Task, task_id)
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")

    was_completed = task.completed
    task.completed = not task.completed
    task.updated_at = datetime.now(timezone.utc)
    session.add(task)
    session.commit()
    session.refresh(task)

    # Publish task.completed event
    if task.completed and not was_completed:
        # Calculate time to complete (hours from created_at to now)
        time_to_complete = None
        if task.created_at:
            delta = task.updated_at - task.created_at
            time_to_complete = delta.total_seconds() / 3600.0

        publish_event(
            event_type="task.completed",
            data={
                "task_id": task.id,
                "user_id": task.user_id,
                "completed": True,
                "completed_at": task.updated_at.isoformat(),
                "time_to_complete_hours": time_to_complete,
            },
            user_id=user_id,
            task_id=task.id,
        )

    return task
