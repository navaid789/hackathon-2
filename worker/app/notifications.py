"""
Notification generation logic for overdue alerts and daily summaries.
"""

import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
from sqlmodel import Session, select, text

from app.models import Notification
from app.db import engine

logger = logging.getLogger(__name__)

# Backend URL for querying tasks (via Dapr service invocation or direct)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")


def create_notification_for_event(
    user_id: str,
    notification_type: str,
    title: str,
    content: str,
    related_task_id: Optional[int],
    session: Session,
) -> Notification:
    """Create and persist a notification."""
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        content=content,
        related_task_id=related_task_id,
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    session.add(notification)
    session.commit()
    session.refresh(notification)
    logger.info(f"Created notification {notification.id} for user {user_id}: {title}")
    return notification


def check_overdue_tasks() -> int:
    """
    Check for overdue tasks and create notifications.
    This queries the tasks table directly (same database).
    Returns the number of notifications created.
    """
    logger.info("Checking for overdue tasks...")
    notifications_created = 0

    # Query tasks that are overdue and not completed
    # Using raw SQL since Task model is in backend
    query = text("""
        SELECT id, user_id, title, due_date
        FROM tasks
        WHERE due_date < :now
          AND completed = false
    """)

    with Session(engine) as session:
        result = session.execute(query, {"now": datetime.now(timezone.utc)})
        overdue_tasks = result.fetchall()

        for task in overdue_tasks:
            task_id, user_id, title, due_date = task

            # Check if we already sent a notification for this task today
            today_start = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            existing = session.exec(
                select(Notification)
                .where(Notification.user_id == user_id)
                .where(Notification.related_task_id == task_id)
                .where(Notification.notification_type == "overdue_alert")
                .where(Notification.created_at >= today_start)
            ).first()

            if existing:
                continue  # Already notified today

            # Create overdue notification
            create_notification_for_event(
                user_id=user_id,
                notification_type="overdue_alert",
                title=f"Overdue: {title}",
                content=f"Task '{title}' was due on {due_date.strftime('%Y-%m-%d') if due_date else 'unknown'}",
                related_task_id=task_id,
                session=session,
            )
            notifications_created += 1

    logger.info(f"Created {notifications_created} overdue notifications")
    return notifications_created


def generate_daily_summary(user_id: str) -> Optional[Notification]:
    """
    Generate a daily summary notification for a user.
    Summarizes tasks created, completed, and pending.
    """
    logger.info(f"Generating daily summary for user {user_id}")

    # Get stats for today
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    query = text("""
        SELECT
            COUNT(*) FILTER (WHERE created_at >= :today_start) as created_today,
            COUNT(*) FILTER (WHERE completed = true AND updated_at >= :today_start) as completed_today,
            COUNT(*) FILTER (WHERE completed = false) as pending_total,
            COUNT(*) FILTER (WHERE due_date < :now AND completed = false) as overdue_total
        FROM tasks
        WHERE user_id = :user_id
    """)

    with Session(engine) as session:
        result = session.execute(
            query,
            {
                "user_id": user_id,
                "today_start": today_start,
                "now": datetime.now(timezone.utc),
            },
        )
        row = result.fetchone()

        if not row:
            return None

        created_today, completed_today, pending_total, overdue_total = row

        # Build summary content
        summary = {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "created_today": created_today or 0,
            "completed_today": completed_today or 0,
            "pending_total": pending_total or 0,
            "overdue_total": overdue_total or 0,
        }

        title = f"Daily Summary: {completed_today or 0} completed, {pending_total or 0} pending"
        content = json.dumps(summary)

        notification = create_notification_for_event(
            user_id=user_id,
            notification_type="daily_summary",
            title=title,
            content=content,
            related_task_id=None,
            session=session,
        )

        return notification


def generate_all_daily_summaries() -> int:
    """
    Generate daily summaries for all active users.
    Returns the number of summaries generated.
    """
    logger.info("Generating daily summaries for all users...")

    # Get distinct user_ids from tasks table
    query = text("SELECT DISTINCT user_id FROM tasks")

    summaries_created = 0
    with Session(engine) as session:
        result = session.execute(query)
        user_ids = [row[0] for row in result.fetchall()]

    for user_id in user_ids:
        try:
            notification = generate_daily_summary(user_id)
            if notification:
                summaries_created += 1
        except Exception as e:
            logger.error(f"Failed to generate summary for user {user_id}: {e}")

    logger.info(f"Generated {summaries_created} daily summaries")
    return summaries_created
