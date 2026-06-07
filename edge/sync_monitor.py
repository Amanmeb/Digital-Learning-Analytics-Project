# School status monitor
# HTTP server on port 8090
# Returns school health status for monitoring dashboard
# Works on Windows, Linux, and Mac

import json
import os
import shutil
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

from edge.queue_manager import get_queue_depth, get_last_sync, create_tables

MONITOR_PORT = int(os.environ.get("MONITOR_PORT", "8090"))
SCHOOL_ID    = os.environ.get("SCHOOL_ID", "ET-AA-001")
SERVER_ID    = os.environ.get("SERVER_ID", "SRV-ET-AA-001-001")

BACKLOG_ALERT_LOW  = int(os.environ.get("BACKLOG_ALERT_LOW", "3"))
BACKLOG_ALERT_MID  = int(os.environ.get("BACKLOG_ALERT_MID", "7"))
BACKLOG_ALERT_HIGH = int(os.environ.get("BACKLOG_ALERT_HIGH", "15"))


def get_disk_space_gb():
    # Returns free disk space in GB
    try:
        usage = shutil.disk_usage("/")
        return round(usage.free / (1024 ** 3), 2)
    except Exception:
        return None


def get_alert_level(last_sync):
    # Returns alert level based on days since last sync
    if not last_sync or not last_sync.get("sync_ended_at"):
        return "unknown"
    try:
        last_sync_time = datetime.fromisoformat(last_sync["sync_ended_at"])
        if last_sync_time.tzinfo is None:
            last_sync_time = last_sync_time.replace(tzinfo=timezone.utc)
        days = (datetime.now(timezone.utc) - last_sync_time).days
        if days >= BACKLOG_ALERT_HIGH:
            return "high"
        elif days >= BACKLOG_ALERT_MID:
            return "medium"
        elif days >= BACKLOG_ALERT_LOW:
            return "low"
        return "ok"
    except Exception:
        return "unknown"


class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status":
            create_tables()
            last_sync = get_last_sync()
            queue_depth = get_queue_depth()
            alert_level = get_alert_level(last_sync)
            disk_space = get_disk_space_gb()

            status = {
                "school_id":    SCHOOL_ID,
                "server_id":    SERVER_ID,
                "status":       "ok" if alert_level in ("ok", "unknown") else "alert",
                "alert_level":  alert_level,
                "queue_depth":  queue_depth,
                "last_sync":    last_sync.get("sync_ended_at") if last_sync else None,
                "last_sync_status": last_sync.get("status") if last_sync else None,
                "disk_space_gb": disk_space,
                "checked_at":   datetime.now(timezone.utc).isoformat(),
            }

            body = json.dumps(status, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default HTTP server logs
        pass


def run():
    server = HTTPServer(("0.0.0.0", MONITOR_PORT), StatusHandler)
    print("School status monitor running on port " + str(MONITOR_PORT))
    server.serve_forever()


if __name__ == "__main__":
    run()
