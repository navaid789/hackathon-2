"""
Background scheduler for periodic tasks:
- Overdue task checks (every 5 minutes)
- Daily summary generation (once per day at configurable time)
"""

import os
import logging
from datetime import datetime, timezone
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Configuration
OVERDUE_CHECK_INTERVAL = int(os.environ.get("OVERDUE_CHECK_INTERVAL", "300"))  # 5 minutes
DAILY_SUMMARY_HOUR = int(os.environ.get("DAILY_SUMMARY_HOUR", "8"))  # 8 AM UTC

# Global state
_scheduler_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()
_last_summary_date: Optional[str] = None


def _run_scheduler():
    """Main scheduler loop."""
    global _last_summary_date

    from app.notifications import check_overdue_tasks, generate_all_daily_summaries

    logger.info("Scheduler started")

    while not _stop_event.is_set():
        try:
            now = datetime.now(timezone.utc)

            # Check for overdue tasks
            logger.debug("Running overdue task check...")
            try:
                check_overdue_tasks()
            except Exception as e:
                logger.error(f"Overdue check failed: {e}")

            # Daily summary (once per day at specified hour)
            today_str = now.strftime("%Y-%m-%d")
            if (
                _last_summary_date != today_str
                and now.hour >= DAILY_SUMMARY_HOUR
            ):
                logger.info("Running daily summary generation...")
                try:
                    generate_all_daily_summaries()
                    _last_summary_date = today_str
                except Exception as e:
                    logger.error(f"Daily summary generation failed: {e}")

        except Exception as e:
            logger.exception(f"Scheduler error: {e}")

        # Wait for next interval or stop signal
        _stop_event.wait(timeout=OVERDUE_CHECK_INTERVAL)

    logger.info("Scheduler stopped")


def start_scheduler():
    """Start the background scheduler thread."""
    global _scheduler_thread

    if _scheduler_thread is not None and _scheduler_thread.is_alive():
        logger.warning("Scheduler already running")
        return

    _stop_event.clear()
    _scheduler_thread = threading.Thread(target=_run_scheduler, daemon=True)
    _scheduler_thread.start()
    logger.info("Scheduler thread started")


def stop_scheduler():
    """Stop the background scheduler thread."""
    global _scheduler_thread

    if _scheduler_thread is None:
        return

    logger.info("Stopping scheduler...")
    _stop_event.set()

    # Wait for thread to finish (with timeout)
    _scheduler_thread.join(timeout=5.0)

    if _scheduler_thread.is_alive():
        logger.warning("Scheduler thread did not stop gracefully")
    else:
        logger.info("Scheduler thread stopped")

    _scheduler_thread = None
