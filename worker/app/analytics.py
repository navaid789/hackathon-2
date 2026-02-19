"""
Analytics bucket management and summary generation.
"""

import logging
from datetime import datetime, timezone, date, timedelta
from typing import Optional, Dict, Any

from sqlmodel import Session, select

from app.models import AnalyticsBucket

logger = logging.getLogger(__name__)


def get_or_create_bucket(
    user_id: str,
    bucket_date: date,
    session: Session,
) -> AnalyticsBucket:
    """Get or create an analytics bucket for a user on a specific date."""
    existing = session.exec(
        select(AnalyticsBucket)
        .where(AnalyticsBucket.user_id == user_id)
        .where(AnalyticsBucket.bucket_date == bucket_date)
    ).first()

    if existing:
        return existing

    # Create new bucket
    bucket = AnalyticsBucket(
        user_id=user_id,
        bucket_date=bucket_date,
        tasks_created=0,
        tasks_completed=0,
        tasks_deleted=0,
        total_completion_time_hours=0.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(bucket)
    session.commit()
    session.refresh(bucket)
    return bucket


def update_analytics_bucket(
    user_id: str,
    session: Session,
    increment_created: int = 0,
    increment_completed: int = 0,
    increment_deleted: int = 0,
    add_completion_time: Optional[float] = None,
) -> AnalyticsBucket:
    """
    Update analytics bucket for the current day.
    Called from event handlers to increment counters.
    """
    today = date.today()
    bucket = get_or_create_bucket(user_id, today, session)

    if increment_created:
        bucket.tasks_created += increment_created
    if increment_completed:
        bucket.tasks_completed += increment_completed
    if increment_deleted:
        bucket.tasks_deleted += increment_deleted
    if add_completion_time is not None and add_completion_time > 0:
        bucket.total_completion_time_hours += add_completion_time

    bucket.updated_at = datetime.now(timezone.utc)
    session.add(bucket)
    session.commit()
    session.refresh(bucket)

    logger.debug(f"Updated analytics bucket for {user_id} on {today}")
    return bucket


def get_analytics_summary(
    user_id: str,
    days: int,
    session: Session,
) -> Dict[str, Any]:
    """
    Get analytics summary for a user over the specified number of days.
    Returns completion rate, average time-to-complete, and daily trends.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    # Get all buckets in range
    buckets = session.exec(
        select(AnalyticsBucket)
        .where(AnalyticsBucket.user_id == user_id)
        .where(AnalyticsBucket.bucket_date >= start_date)
        .where(AnalyticsBucket.bucket_date <= end_date)
        .order_by(AnalyticsBucket.bucket_date)
    ).all()

    # Aggregate stats
    total_created = sum(b.tasks_created for b in buckets)
    total_completed = sum(b.tasks_completed for b in buckets)
    total_deleted = sum(b.tasks_deleted for b in buckets)
    total_completion_time = sum(b.total_completion_time_hours for b in buckets)

    # Calculate derived metrics
    completion_rate = 0.0
    if total_created > 0:
        completion_rate = (total_completed / total_created) * 100

    avg_completion_time = 0.0
    if total_completed > 0:
        avg_completion_time = total_completion_time / total_completed

    # Build daily trend data
    daily_trends = []
    for b in buckets:
        daily_trends.append({
            "date": b.bucket_date.isoformat(),
            "tasks_created": b.tasks_created,
            "tasks_completed": b.tasks_completed,
            "tasks_deleted": b.tasks_deleted,
        })

    # Fill in missing days with zeros
    existing_dates = {b.bucket_date for b in buckets}
    current = start_date
    while current <= end_date:
        if current not in existing_dates:
            daily_trends.append({
                "date": current.isoformat(),
                "tasks_created": 0,
                "tasks_completed": 0,
                "tasks_deleted": 0,
            })
        current += timedelta(days=1)

    # Sort by date
    daily_trends.sort(key=lambda x: x["date"])

    return {
        "user_id": user_id,
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "summary": {
            "total_created": total_created,
            "total_completed": total_completed,
            "total_deleted": total_deleted,
            "completion_rate_percent": round(completion_rate, 1),
            "avg_completion_time_hours": round(avg_completion_time, 2),
        },
        "daily_trends": daily_trends,
    }
