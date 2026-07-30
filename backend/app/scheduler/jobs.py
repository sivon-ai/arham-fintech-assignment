import logging
from datetime import datetime, timezone

from app.scheduler.state import state
from app.services.live import live_hub
from app.services.sync import SyncService

logger = logging.getLogger(__name__)


def sync_job():

    with state.lock:
        if state.sync_running:
            logger.warning("Previous sync still running. Skipping...")
            return

        state.sync_running = True
        state.last_status = "RUNNING"
        state.last_error = None

    try:
        logger.info("Starting scheduled sync...")
        counts = SyncService().sync_all()

        with state.lock:
            state.last_sync = datetime.now(timezone.utc).isoformat()
            state.last_status = "SUCCESS"
            state.last_error = None
            state.last_counts = counts
            state.version += 1

        live_hub.publish(
            {
                "type": "sync_complete",
                "version": state.snapshot()["version"],
                "counts": counts,
            }
        )
        logger.info("Sync completed successfully.")

    except Exception as e:
        logger.exception(e)

        with state.lock:
            state.last_status = "FAILED"
            state.last_error = str(e)

        live_hub.publish(
            {
                "type": "sync_failed",
                "error": str(e),
                "version": state.snapshot()["version"],
            }
        )

    finally:
        with state.lock:
            state.sync_running = False
