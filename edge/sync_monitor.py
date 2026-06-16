# School status monitor
# HTTP server on port 8090
# Returns school health status for monitoring dashboard
# Provides on-demand CSV export of queued events by date range
# Provides self-install page for device agent at /install
# Works on Windows, Linux, and Mac

import csv
import io
import json
import os
import shutil
import sqlite3
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from edge.queue_manager import get_queue_depth, get_last_sync, create_tables, get_db_path

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


def export_events_csv(from_date, to_date):
    # Exports all events from SQLite queue within date range
    # Returns CSV bytes regardless of sync status
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT
            id,
            fingerprint,
            statement,
            synced,
            created_at
        FROM events
        WHERE date(created_at) >= date(:from_date)
        AND date(created_at) <= date(:to_date)
        ORDER BY created_at
    """, {"from_date": from_date, "to_date": to_date})
    rows = cur.fetchall()
    conn.close()
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))
    else:
        output.write("id,fingerprint,statement,synced,created_at\n")
    return output.getvalue().encode("utf-8")


EXPORT_FORM_HTML = """<!DOCTYPE html>
<html>
<head><title>CDLAID School Data Export</title>
<style>
body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; }}
h2 {{ color: #375C7A; }}
label {{ display: block; margin-top: 15px; font-weight: bold; }}
input {{ width: 100%; padding: 8px; margin-top: 5px; border: 1px solid #ccc; border-radius: 4px; }}
button {{ margin-top: 20px; padding: 10px 30px; background: #81BC00; color: white;
          border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }}
button:hover {{ background: #6a9e00; }}
.info {{ background: #f0f7e6; padding: 10px; border-radius: 4px; margin-top: 20px; font-size: 14px; }}
</style>
</head>
<body>
<h2>School Data Export</h2>
<p>School ID: <strong>{school_id}</strong></p>
<p>Export all learning events from this school for the selected date range.
   Send the downloaded file to your central admin for manual import.</p>
<form method="get" action="/export/download">
<label>From Date</label>
<input type="date" name="from_date" required value="{default_from}">
<label>To Date</label>
<input type="date" name="to_date" required value="{default_to}">
<button type="submit">Download CSV</button>
</form>
<div class="info">
The export includes all events in the selected range regardless of sync status.
The central admin will use deduplication to avoid any duplicates.
</div>
</body>
</html>"""


INSTALL_PAGE_HTML = """<!DOCTYPE html>
<html>
<head><title>CDLAID Device Agent Install</title>
<style>
body {{ font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 20px; }}
h2 {{ color: #375C7A; }}
h3 {{ color: #81BC00; margin-top: 30px; }}
.card {{ background: #f0f7e6; border: 1px solid #81BC00; border-radius: 8px;
         padding: 20px; margin-top: 20px; }}
.card-blue {{ background: #eaf0f6; border: 1px solid #375C7A; border-radius: 8px;
              padding: 20px; margin-top: 20px; }}
a.btn {{ display: inline-block; padding: 12px 28px; background: #81BC00; color: white;
         text-decoration: none; border-radius: 4px; font-size: 16px; margin-top: 10px; }}
a.btn:hover {{ background: #6a9e00; }}
a.btn-blue {{ background: #375C7A; }}
a.btn-blue:hover {{ background: #2a4560; }}
p {{ line-height: 1.6; }}
code {{ background: #eee; padding: 2px 6px; border-radius: 3px; font-size: 14px; }}
.qr {{ text-align: center; margin-top: 20px; }}
.qr img {{ width: 200px; height: 200px; border: 1px solid #ccc; padding: 10px; }}
.step {{ background: #fff; border-left: 4px solid #81BC00; padding: 10px 15px;
         margin-top: 10px; }}
</style>
</head>
<body>
<h2>Camara Learning -- Device Agent Installer</h2>
<p>School ID: <strong>{school_id}</strong> | Server: <strong>{server_id}</strong></p>
<p>Install the Camara Device Agent so your device can sync learning data
   to the school server even when offline. Choose your device type below.</p>

<div class="card">
<h3>Windows PC</h3>
<p>For Windows student lab computers.</p>
<div class="step">Step 1 -- Download the installer below</div>
<div class="step">Step 2 -- Right-click the file and select Run as Administrator</div>
<div class="step">Step 3 -- Follow the prompts and enter the school details when asked</div>
<div class="step">Step 4 -- The agent starts automatically and syncs when connected to {hotspot_name}</div>
<br>
<a class="btn" href="/install/download/windows">Download Windows Installer (.bat)</a>
</div>

<div class="card">
<h3>Linux PC (Ubuntu)</h3>
<p>For Ubuntu student lab computers.</p>
<div class="step">Step 1 -- Download the installer below</div>
<div class="step">Step 2 -- Open a terminal and run: <code>sudo bash install_device.sh</code></div>
<div class="step">Step 3 -- Follow the prompts and enter the school details when asked</div>
<div class="step">Step 4 -- The agent starts automatically and syncs when connected to {hotspot_name}</div>
<br>
<a class="btn" href="/install/download/linux">Download Linux Installer (.sh)</a>
</div>

<div class="card-blue">
<h3>Android Tablet or Chromebook</h3>
<p>No install needed. Open Chrome browser and scan this QR code or visit the URL below.</p>
<p>The Camara Learning app will install automatically in Chrome.</p>
<div class="qr">
<p><strong>Scan to open Moodle:</strong></p>
<img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=http://10.42.0.1:3000"
     alt="QR code for http://10.42.0.1:3000">
<p><code>http://10.42.0.1:3000</code></p>
</div>
</div>

<div class="card">
<h3>Need Help?</h3>
<p>Contact your school ICT coordinator or Camara technical support.</p>
<p>School status: <a href="/status">http://10.42.0.1:8090/status</a></p>
<p>Data export: <a href="/export">http://10.42.0.1:8090/export</a></p>
</div>

</body>
</html>"""


class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/status":
            create_tables()
            last_sync = get_last_sync()
            queue_depth = get_queue_depth()
            alert_level = get_alert_level(last_sync)
            disk_space = get_disk_space_gb()
            status = {
                "school_id":        SCHOOL_ID,
                "server_id":        SERVER_ID,
                "status":           "ok" if alert_level in ("ok", "unknown") else "alert",
                "alert_level":      alert_level,
                "queue_depth":      queue_depth,
                "last_sync":        last_sync.get("sync_ended_at") if last_sync else None,
                "last_sync_status": last_sync.get("status") if last_sync else None,
                "disk_space_gb":    disk_space,
                "checked_at":       datetime.now(timezone.utc).isoformat(),
            }
            body = json.dumps(status, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif parsed.path == "/export":
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            thirty_days_ago = (
                datetime.now(timezone.utc) - timedelta(days=30)
            ).strftime("%Y-%m-%d")
            html = EXPORT_FORM_HTML.format(
                school_id=SCHOOL_ID,
                default_from=thirty_days_ago,
                default_to=today,
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)

        elif parsed.path == "/export/download":
            from_date = params.get("from_date", [None])[0]
            to_date   = params.get("to_date", [None])[0]
            if not from_date or not to_date:
                body = b"Missing from_date or to_date parameters"
                self.send_response(400)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            try:
                csv_bytes = export_events_csv(from_date, to_date)
                filename = (
                    "cdlaid_export_" + SCHOOL_ID +
                    "_" + from_date + "_to_" + to_date + ".csv"
                )
                self.send_response(200)
                self.send_header("Content-Type", "text/csv")
                self.send_header(
                    "Content-Disposition", "attachment; filename=" + filename
                )
                self.send_header("Content-Length", str(len(csv_bytes)))
                self.end_headers()
                self.wfile.write(csv_bytes)
            except Exception as e:
                body = ("Export failed: " + str(e)).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        elif parsed.path == "/install":
            # Self-install page for device agent
            # Serves download links for Windows and Linux installers
            # Serves QR code for PWA on Android and Chromebook
            hotspot_name = "Camara-" + SCHOOL_ID
            html = INSTALL_PAGE_HTML.format(
                school_id=SCHOOL_ID,
                server_id=SERVER_ID,
                hotspot_name=hotspot_name,
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)

        elif parsed.path == "/install/download/windows":
            # Serves the Windows installer batch file for download
            installer_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "scripts", "install_device.bat"
            )
            try:
                with open(installer_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header(
                    "Content-Disposition",
                    "attachment; filename=install_device.bat"
                )
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                body = ("Installer not found: " + str(e)).encode("utf-8")
                self.send_response(404)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        elif parsed.path == "/install/download/linux":
            # Serves the Linux installer shell script for download
            installer_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "scripts", "install_device.sh"
            )
            try:
                with open(installer_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header(
                    "Content-Disposition",
                    "attachment; filename=install_device.sh"
                )
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                body = ("Installer not found: " + str(e)).encode("utf-8")
                self.send_response(404)
                self.send_header("Content-Type", "text/plain")
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