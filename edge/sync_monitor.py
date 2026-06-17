# School status monitor
# HTTP server on port 8090
# Returns school health status for monitoring dashboard
# Provides on-demand CSV export of queued events by date range
# Provides self-install page for device agent, Moodle app, and PWA
# Serves PWA files (manifest, service worker, sync queue, offline page)
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
MOODLE_URL   = os.environ.get("MOODLE_URL", "http://10.42.0.1:3000")
BACKLOG_ALERT_LOW  = int(os.environ.get("BACKLOG_ALERT_LOW", "3"))
BACKLOG_ALERT_MID  = int(os.environ.get("BACKLOG_ALERT_MID", "7"))
BACKLOG_ALERT_HIGH = int(os.environ.get("BACKLOG_ALERT_HIGH", "15"))

# MIME types for serving PWA static files
PWA_MIME_TYPES = {
    ".json": "application/json",
    ".js":   "application/javascript",
    ".html": "text/html; charset=utf-8",
    ".png":  "image/png",
}


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
<head>
<title>Camara Learning - Get Started</title>
<link rel="manifest" href="/pwa/manifest.json">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {{ font-family: Arial, sans-serif; max-width: 750px; margin: 30px auto; padding: 20px; }}
h2 {{ color: #375C7A; }}
h3 {{ color: #81BC00; margin-top: 30px; }}
.card {{ background: #f0f7e6; border: 1px solid #81BC00; border-radius: 8px;
         padding: 20px; margin-top: 20px; }}
.card-blue {{ background: #eaf0f6; border: 1px solid #375C7A; border-radius: 8px;
              padding: 20px; margin-top: 20px; }}
.card-purple {{ background: #f3eaf0; border: 1px solid #943266; border-radius: 8px;
                padding: 20px; margin-top: 20px; }}
a.btn {{ display: inline-block; padding: 12px 28px; background: #81BC00; color: white;
         text-decoration: none; border-radius: 4px; font-size: 16px; margin-top: 10px; }}
a.btn:hover {{ background: #6a9e00; }}
a.btn-blue {{ background: #375C7A; }}
a.btn-blue:hover {{ background: #2a4560; }}
a.btn-purple {{ background: #943266; }}
a.btn-purple:hover {{ background: #732650; }}
p {{ line-height: 1.6; }}
code {{ background: #eee; padding: 2px 6px; border-radius: 3px; font-size: 14px; }}
.qr {{ text-align: center; margin-top: 20px; }}
.qr img {{ width: 180px; height: 180px; border: 1px solid #ccc; padding: 10px;
           background: white; }}
.step {{ background: #fff; border-left: 4px solid #81BC00; padding: 10px 15px;
         margin-top: 10px; }}
.step-blue {{ border-left-color: #375C7A; }}
.step-purple {{ border-left-color: #943266; }}
#pwa-install-btn {{ display: none; }}
</style>
</head>
<body>
<h2>Camara Learning -- Get Started</h2>
<p>School ID: <strong>{school_id}</strong> | Server: <strong>{server_id}</strong></p>
<p>Choose the option below that matches your device. All options work
   offline and sync automatically when connected to {hotspot_name}.</p>

<div class="card">
<h3>Install as an App (Android and Chromebook)</h3>
<p>Install Camara Learning directly to your home screen with one tap.
   Works offline using your browser, no Play Store needed.</p>
<button id="pwa-install-btn" onclick="installPwa()">Install Camara Learning App</button>
<p id="pwa-status"></p>
</div>

<div class="card-blue">
<h3>Moodle App (Android)</h3>
<div class="step step-blue">Step 1 -- Download the Moodle app from Google Play Store</div>
<div class="step step-blue">Step 2 -- Open the app and enter the site URL: <code>{moodle_url}</code></div>
<div class="step step-blue">Step 3 -- Log in with your student username and password</div>
<div class="step step-blue">Step 4 -- Download courses for offline use from the course menu</div>
<br>
<a class="btn btn-blue" href="https://play.google.com/store/apps/details?id=com.moodle.moodlemobile" target="_blank">
Get Moodle App on Google Play</a>
</div>

<div class="card-blue">
<h3>Moodle App (iPhone and iPad)</h3>
<div class="step step-blue">Step 1 -- Download the Moodle app from the App Store</div>
<div class="step step-blue">Step 2 -- Open the app and enter the site URL: <code>{moodle_url}</code></div>
<div class="step step-blue">Step 3 -- Log in with your student username and password</div>
<div class="step step-blue">Step 4 -- Download courses for offline use from the course menu</div>
<br>
<a class="btn btn-blue" href="https://apps.apple.com/app/moodle/id633359593" target="_blank">
Get Moodle App on App Store</a>
</div>

<div class="card-purple">
<h3>Windows PC</h3>
<p>For Windows student lab computers.</p>
<div class="step step-purple">Step 1 -- Download the installer below</div>
<div class="step step-purple">Step 2 -- Right-click the file and select Run as Administrator</div>
<div class="step step-purple">Step 3 -- Follow the prompts and enter the school details when asked</div>
<div class="step step-purple">Step 4 -- The agent starts automatically and syncs when connected to {hotspot_name}</div>
<br>
<a class="btn btn-purple" href="/install/download/windows">Download Windows Installer (.bat)</a>
</div>

<div class="card-purple">
<h3>Linux PC (Ubuntu)</h3>
<p>For Ubuntu student lab computers.</p>
<div class="step step-purple">Step 1 -- Download the installer below</div>
<div class="step step-purple">Step 2 -- Open a terminal and run: <code>sudo bash install_device.sh</code></div>
<div class="step step-purple">Step 3 -- Follow the prompts and enter the school details when asked</div>
<div class="step step-purple">Step 4 -- The agent starts automatically and syncs when connected to {hotspot_name}</div>
<br>
<a class="btn btn-purple" href="/install/download/linux">Download Linux Installer (.sh)</a>
</div>

<div class="card">
<h3>Scan to Open Moodle Directly</h3>
<p>Scan this code with your phone camera to open the school Moodle site
   in your browser.</p>
<div class="qr">
<img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={moodle_url}"
     alt="QR code for {moodle_url}">
<p><code>{moodle_url}</code></p>
</div>
</div>

<div class="card">
<h3>Need Help?</h3>
<p>Contact your school ICT coordinator or Camara technical support.</p>
<p>School status: <a href="/status">/status</a></p>
<p>Data export: <a href="/export">/export</a></p>
</div>

<script src="/pwa/sync_queue.js"></script>
<script>
var deferredPrompt;

if ("serviceWorker" in navigator) {{
    navigator.serviceWorker.register("/pwa/service_worker.js").then(function () {{
        document.getElementById("pwa-status").innerText = "Offline mode ready.";
    }}).catch(function () {{
        document.getElementById("pwa-status").innerText =
            "Offline mode could not be enabled on this browser.";
    }});
}}

window.addEventListener("beforeinstallprompt", function (event) {{
    event.preventDefault();
    deferredPrompt = event;
    document.getElementById("pwa-install-btn").style.display = "inline-block";
}});

function installPwa() {{
    if (!deferredPrompt) {{
        document.getElementById("pwa-status").innerText =
            "App install is not available on this browser. " +
            "Open this page in Chrome on Android.";
        return;
    }}
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then(function (choiceResult) {{
        if (choiceResult.outcome === "accepted") {{
            document.getElementById("pwa-status").innerText = "App installed successfully.";
        }}
        deferredPrompt = null;
        document.getElementById("pwa-install-btn").style.display = "none";
    }});
}}
</script>

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
            # Self-install page showing all access options
            # Moodle app for Android and iPhone, PWA install, QR code,
            # Windows and Linux device agent downloads
            hotspot_name = "Camara-" + SCHOOL_ID
            html = INSTALL_PAGE_HTML.format(
                school_id=SCHOOL_ID,
                server_id=SERVER_ID,
                hotspot_name=hotspot_name,
                moodle_url=MOODLE_URL,
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)

        elif parsed.path == "/install/download/windows":
            self._serve_installer("install_device.bat")

        elif parsed.path == "/install/download/linux":
            self._serve_installer("install_device.sh")

        elif parsed.path.startswith("/pwa/"):
            self._serve_pwa_file(parsed.path)

        else:
            self.send_response(404)
            self.end_headers()

    def _serve_installer(self, filename):
        # Serves an installer script file for download
        installer_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts", filename
        )
        try:
            with open(installer_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header(
                "Content-Disposition", "attachment; filename=" + filename
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

    def _serve_pwa_file(self, path):
        # Serves a static PWA file from the pwa/ folder
        # Handles manifest, service worker, sync queue, offline page, icon
        filename = path.replace("/pwa/", "", 1)
        pwa_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "pwa"
        )
        file_path = os.path.join(pwa_dir, filename)

        # Prevent directory traversal outside the pwa folder
        if not os.path.abspath(file_path).startswith(os.path.abspath(pwa_dir)):
            self.send_response(403)
            self.end_headers()
            return

        extension = os.path.splitext(filename)[1]
        content_type = PWA_MIME_TYPES.get(extension, "application/octet-stream")

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Service-Worker-Allowed", "/")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            body = ("PWA file not found: " + str(e)).encode("utf-8")
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, format, *args):
        # Suppress default HTTP server logs
        pass


def run():
    server = HTTPServer(("0.0.0.0", MONITOR_PORT), StatusHandler)
    print("School status monitor running on port " + str(MONITOR_PORT))
    server.serve_forever()


if __name__ == "__main__":
    run()