from threading import Lock


class SchedulerState:

    def __init__(self):
        self.lock = Lock()
        self.sync_running = False
        self.last_sync = None
        self.last_status = "Never"
        self.last_error = None
        self.last_error = None
        self.last_counts = {}
        self.version = 0

    def snapshot(self):
        with self.lock:
            return {
                "sync_running": self.sync_running,
                "last_sync": self.last_sync,
                "last_status": self.last_status,
                "last_error": self.last_error,
                "last_counts": self.last_counts,
                "version": self.version,
            }


state = SchedulerState()
