from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate
from app.auth import verify_token, get_user_id

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
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    task.updated_at = datetime.now(timezone.utc)
    session.add(task)
    session.commit()
    session.refresh(task)
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
    session.delete(task)
    session.commit()


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
    task.completed = not task.completed
    task.updated_at = datetime.now(timezone.utc)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task
