import os
import logging
from uuid import uuid4
from datetime import datetime, timezone
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)

# Dapr sidecar runs at localhost:3500
DAPR_HTTP_PORT = os.environ.get("DAPR_HTTP_PORT", "3500")
DAPR_PUBSUB_NAME = os.environ.get("DAPR_PUBSUB_NAME", "taskflow-pubsub")
DAPR_TOPIC = os.environ.get("DAPR_TOPIC", "task-events")
DAPR_URL = f"http://localhost:{DAPR_HTTP_PORT}/v1.0/publish/{DAPR_PUBSUB_NAME}/{DAPR_TOPIC}"


def publish_event(
    event_type: str,
    data: Dict[str, Any],
    user_id: str,
    task_id: int,
) -> None:
    """
    Publish an event to Dapr pub/sub.

    Fire-and-forget: if publishing fails, log a warning but do not fail the request.
    The primary database operation has already succeeded.
    """
    event_id = str(uuid4())

    # CloudEvents envelope - Dapr adds specversion, source, time automatically
    # We provide: type, data, and optional metadata
    payload = {
        "id": event_id,
        "type": event_type,
        "data": data,
        "datacontenttype": "application/json",
    }

    try:
        # Use a short timeout to avoid blocking the request
        with httpx.Client(timeout=2.0) as client:
            response = client.post(
                DAPR_URL,
                json=payload,
                headers={"Content-Type": "application/cloudevents+json"},
            )
            if response.status_code in (200, 201, 204):
                logger.info(f"Published event {event_type} for task {task_id}, event_id={event_id}")
            else:
                logger.warning(
                    f"Failed to publish event {event_type}: {response.status_code} {response.text}"
                )
    except httpx.ConnectError:
        # Dapr sidecar not running (local dev without Dapr)
        logger.warning(f"Dapr sidecar not available, skipping event publish for {event_type}")
    except Exception as e:
        # Log but don't fail - the DB operation already succeeded
        logger.warning(f"Event publish failed for {event_type}: {type(e).__name__}: {e}")
