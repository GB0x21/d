import time
import logging

logger = logging.getLogger(__name__)


class HealthMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.posts_processed = 0
        self.alerts_sent = 0
        self.errors = 0
        self.last_post_time = None
        self.last_error = None

    def record_post(self):
        self.posts_processed += 1
        self.last_post_time = time.time()

    def record_alert(self):
        self.alerts_sent += 1

    def record_error(self, error: str):
        self.errors += 1
        self.last_error = error
        logger.error("Health: error recorded - %s", error)

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self.start_time

    @property
    def uptime_str(self) -> str:
        s = int(self.uptime_seconds)
        hours, remainder = divmod(s, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours}h {minutes}m {secs}s"

    @property
    def is_stale(self) -> bool:
        if self.last_post_time is None:
            return self.uptime_seconds > 600  # 10 min without any post
        return (time.time() - self.last_post_time) > 600

    def get_status_report(self) -> str:
        status = "STALE" if self.is_stale else "OK"
        return (
            f"PennyBot Health Report\n"
            f"Status: {status}\n"
            f"Uptime: {self.uptime_str}\n"
            f"Posts processed: {self.posts_processed}\n"
            f"Alerts sent: {self.alerts_sent}\n"
            f"Errors: {self.errors}\n"
            f"Last error: {self.last_error or 'None'}"
        )
