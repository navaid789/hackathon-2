"""
Event handler module for processing task events.
Implements idempotency via ProcessedEvent deduplication table.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any

from sqlmodel import Session

from app.models import ProcessedEvent
from app.notifications import create_notification_for_event
from app.analytics import update_analytics_bucket

logger = logging.getLogger(__name__)


def is_event_processed(event_id: str, session: Session) -> bool:
    """Check if an event has already been processed (idempotency check)."""
    existing = session.get(ProcessedEvent, event_id)
    return existing is not None


def mark_event_processed(event_id: str, session: Session) -> None:
    """Mark an event as processed."""
    processed = ProcessedEvent(
        event_id=event_id,
        processed_at=datetime.now(timezone.utc),
    )
    session.add(processed)
    session.commit()


def handle_event(
    event_id: str,
    event_type: str,
    data: Dict[str, Any],
    session: Session,
) -> bool:
    """
    Main event handler with idempotency check.
    Returns True if event was processed, False if skipped (already processed).
    """
    # Idempotency check
    if is_event_processed(event_id, session):
        logger.info(f"Event {event_id} already processed, skipping")
        return False

    logger.info(f"Processing event {event_id} of type {event_type}")

    try:
        # Dispatch to appropriate handler
        if event_type == "task.created":
            handle_task_created(data, session)
        elif event_type == "task.updated":
            handle_task_updated(data, session)
        elif event_type == "task.completed":
            handle_task_completed(data, session)
        elif event_type == "task.deleted":
            handle_task_deleted(data, session)
        else:
            logger.warning(f"Unknown event type: {event_type}")

        # Mark as processed
        mark_event_processed(event_id, session)
        return True

    except Exception as e:
        logger.exception(f"Error handling event {event_id}: {e}")
        raise


def handle_task_created(data: Dict[str, Any], session: Session) -> None:
    """Handle task.created event."""
    user_id = data.get("user_id")
    task_id = data.get("task_id")
    title = data.get("title", "Untitled")

    logger.info(f"Task created: {task_id} for user {user_id}")

    # Update analytics
    update_analytics_bucket(
        user_id=user_id,
        increment_created=1,
        session=session,
    )

    # Check if task is already overdue at creation (has past due date)
    due_date_str = data.get("due_date")
    if due_date_str:
        try:
            due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
            if due_date < datetime.now(timezone.utc):
                create_notification_for_event(
                    user_id=user_id,
                    notification_type="overdue_alert",
                    title=f"Task already overdue: {title}",
                    content=f"The task '{title}' was created with a due date in the past.",
                    related_task_id=task_id,
                    session=session,
                )
        except (ValueError, TypeError):
            pass  # Invalid date format, ignore


def handle_task_updated(data: Dict[str, Any], session: Session) -> None:
    """Handle task.updated event."""
    user_id = data.get("user_id")
    task_id = data.get("task_id")
    changes = data.get("changes", {})

    logger.info(f"Task updated: {task_id} for user {user_id}, changes: {changes}")

    # If due_date was changed, check if now overdue
    if "due_date" in changes:
        new_due_date_str = changes["due_date"].get("new")
        if new_due_date_str:
            try:
                due_date = datetime.fromisoformat(new_due_date_str.replace("Z", "+00:00"))
                if due_date < datetime.now(timezone.utc):
                    create_notification_for_event(
                        user_id=user_id,
                        notification_type="overdue_alert",
                        title="Task due date changed to past",
                        content=f"Task {task_id} now has a due date in the past.",
                        related_task_id=task_id,
                        session=session,
                    )
            except (ValueError, TypeError):
                pass


def handle_task_completed(data: Dict[str, Any], session: Session) -> None:
    """Handle task.completed event."""
    user_id = data.get("user_id")
    task_id = data.get("task_id")
    time_to_complete = data.get("time_to_complete_hours")

    logger.info(f"Task completed: {task_id} for user {user_id}")

    # Update analytics
    update_analytics_bucket(
        user_id=user_id,
        increment_completed=1,
        add_completion_time=time_to_complete,
        session=session,
    )


def handle_task_deleted(data: Dict[str, Any], session: Session) -> None:
    """Handle task.deleted event."""
    user_id = data.get("user_id")
    task_id = data.get("task_id")
    title = data.get("title", "Unknown")

    logger.info(f"Task deleted: {task_id} ({title}) for user {user_id}")

    # Update analytics
    update_analytics_bucket(
        user_id=user_id,
        increment_deleted=1,
        session=session,
    )
