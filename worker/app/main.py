import os
import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from app.db import create_db_and_tables, get_session, engine
from app.models import Notification, ProcessedEvent
from app.events import handle_event
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DAPR_PUBSUB_NAME = os.environ.get("DAPR_PUBSUB_NAME", "taskflow-pubsub")
DAPR_TOPIC = os.environ.get("DAPR_TOPIC", "task-events")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Worker starting up...")
    create_db_and_tables()
    start_scheduler()
    yield
    # Shutdown
    logger.info("Worker shutting down...")
    stop_scheduler()


app = FastAPI(
    title="TaskFlow Worker",
    description="Event-driven worker for notifications and analytics",
    version="1.0.0",
    lifespan=lifespan,
)


# =============================================================================
# Health Check
# =============================================================================


@app.get("/health")
def health_check():
    """Health check endpoint for orchestrators."""
    # Check database connectivity
    db_healthy = False
    try:
        with Session(engine) as session:
            session.exec(select(ProcessedEvent).limit(1))
            db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    status = "healthy" if db_healthy else "degraded"
    return {
        "status": status,
        "service": "worker",
        "checks": {
            "database": "ok" if db_healthy else "error",
        },
    }


# =============================================================================
# Dapr Subscription Endpoint (T024)
# =============================================================================


@app.get("/dapr/subscribe")
def dapr_subscribe():
    """
    Dapr subscription endpoint.
    Dapr calls this at startup to discover which topics this app subscribes to.
    """
    return [
        {
            "pubsubname": DAPR_PUBSUB_NAME,
            "topic": DAPR_TOPIC,
            "route": "/events/task",
        }
    ]


# =============================================================================
# Event Receiver Endpoint (T025)
# =============================================================================


@app.post("/events/task")
async def receive_task_event(request: Request, session: Session = Depends(get_session)):
    """
    Receive task events from Dapr pub/sub.
    CloudEvents envelope is unwrapped by Dapr; we receive the inner payload.
    """
    try:
        body = await request.json()
        logger.info(f"Received event: {body}")

        # Dapr sends CloudEvents - extract the data
        event_id = body.get("id")
        event_type = body.get("type")
        data = body.get("data", {})

        if not event_id or not event_type:
            logger.warning(f"Invalid event format: {body}")
            return JSONResponse(content={"status": "DROP"}, status_code=200)

        # Handle the event (idempotency checked inside)
        success = handle_event(
            event_id=event_id,
            event_type=event_type,
            data=data,
            session=session,
        )

        if success:
            return JSONResponse(content={"status": "SUCCESS"}, status_code=200)
        else:
            # Return SUCCESS to acknowledge (already processed or non-critical)
            return JSONResponse(content={"status": "SUCCESS"}, status_code=200)

    except Exception as e:
        logger.exception(f"Error processing event: {e}")
        # Return RETRY to have Dapr retry the message
        return JSONResponse(content={"status": "RETRY"}, status_code=500)


# =============================================================================
# Notifications API (T031-T032)
# =============================================================================


@app.get("/api/notifications/{user_id}")
def list_notifications(
    user_id: str,
    unread_only: bool = False,
    limit: int = 50,
    session: Session = Depends(get_session),
) -> List[dict]:
    """Get notifications for a user."""
    query = select(Notification).where(Notification.user_id == user_id)

    if unread_only:
        query = query.where(Notification.is_read == False)

    query = query.order_by(Notification.created_at.desc()).limit(limit)
    notifications = session.exec(query).all()

    return [
        {
            "id": n.id,
            "user_id": n.user_id,
            "notification_type": n.notification_type,
            "title": n.title,
            "content": n.content,
            "related_task_id": n.related_task_id,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications
    ]


@app.patch("/api/notifications/{user_id}/{notification_id}/read")
def mark_notification_read(
    user_id: str,
    notification_id: int,
    session: Session = Depends(get_session),
):
    """Mark a notification as read."""
    notification = session.get(Notification, notification_id)

    if not notification or notification.user_id != user_id:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    session.add(notification)
    session.commit()
    session.refresh(notification)

    return {
        "id": notification.id,
        "is_read": notification.is_read,
    }


# =============================================================================
# Analytics API (T047 - implemented here for completeness)
# =============================================================================


@app.get("/api/analytics/{user_id}")
def get_analytics(
    user_id: str,
    days: int = 7,
    session: Session = Depends(get_session),
):
    """Get analytics summary for a user."""
    from app.analytics import get_analytics_summary

    return get_analytics_summary(user_id=user_id, days=days, session=session)
