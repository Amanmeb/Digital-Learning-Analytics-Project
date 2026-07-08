# CDLAID Device Tracker
# Background monitoring thread for student devices
# Tracks active application, website, and idle state
# Runs alongside device_agent.py -- called from the same process
# Emits xAPI events into the local SQLite queue via insert_event()
# Student identity is set by the login app via a tiny localhost HTTP API
# on port 8091 after the student logs in at the school server URL
import platform
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

IDLE_THRESHOLD_SECONDS = 5 * 60
AUTO_LOGOUT_SECONDS = 30 * 60
CHECK_INTERVAL_SECONDS = 5
IDENTITY_API_PORT = 8091
CAMARA_VERB_BASE = "https://camara.org/xapi/verbs"
CAMARA_CONTEXT_EXT = "https://camara.org/xapi/context"
ACTIVITY_BASE = "https://camara.org/xapi/activities"

_current_student_id = None
_current_session_id = None
_lock = threading.Lock()


def set_student_identity(student_id, session_id):
    # Called when a student logs in via the login app
    global _current_student_id, _current_session_id
    with _lock:
        _current_student_id = student_id
        _current_session_id = session_id


def get_student_identity():
    # Returns (student_id, session_id) or (None, None) if not logged in
    with _lock:
        return _current_student_id, _current_session_id


def clear_student_identity():
    # Called on logout or auto-logout
    global _current_student_id, _current_session_id
    with _lock:
        _current_student_id = None
        _current_session_id = None


def now_iso():
    # Returns current UTC time in ISO 8601 format
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_statement(student_id, verb_slug, object_id, object_name,
                    object_type, school_id, device_id, server_id,
                    result=None, extra_context=None):
    # Builds an xAPI statement dict matching the existing emitter format
    import uuid
    context_ext = {
        "school_id":      school_id,
        "device_id":      device_id,
        "platform_id":    "native_agent",
        "is_offline":     True,
        "server_id":      server_id,
        "tracking_depth": "full",
    }
    if extra_context:
        context_ext.update(extra_context)

    statement = {
        "id":        str(uuid.uuid4()),
        "timestamp": now_iso(),
        "actor": {
            "objectType": "Agent",
            "account": {
                "name":     student_id,
                "homePage": "http://10.42.0.1:3000",
            },
        },
        "verb": {
            "id":      CAMARA_VERB_BASE + "/" + verb_slug,
            "display": {"en-US": verb_slug.replace("-", " ")},
        },
        "object": {
            "id":         object_id,
            "objectType": "Activity",
            "definition": {
                "name": {"en-US": object_name},
                "type": ACTIVITY_BASE + "/types/" + object_type,
            },
        },
        "context": {
            "extensions": {
                CAMARA_CONTEXT_EXT: context_ext,
            },
        },
    }
    if result:
        statement["result"] = result
    return statement


def get_active_window_windows():
    # Returns (window_title, process_name) of the foreground window on Windows
    # Returns ("", "") if detection fails
    # Uses PowerShell Get-Process instead of wmic, since wmic has been
    # removed from recent Windows 11 builds -- discovered via live
    # device testing, where wmic silently failed and returned no data.
    # timeout is 8s (not 3s) because spawning a fresh PowerShell process
    # has real startup overhead that can exceed 3 seconds -- also found
    # via live testing, where a 3s timeout caused every single call to
    # silently fail with TimeoutExpired.
    try:
        import ctypes
        import ctypes.wintypes
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value

        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

        import subprocess
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-Process -Id " + str(pid.value) + ").ProcessName"],
            capture_output=True, text=True, timeout=8,
        )
        process_name = result.stdout.strip()
        return title, process_name
    except Exception:
        return "", ""


def get_active_window_linux():
    # Returns (window_title, process_name) of the active window on Linux
    # Uses xdotool if available, otherwise returns empty strings
    try:
        import subprocess
        win_id_result = subprocess.run(
            ["xdotool", "getactivewindow"],
            capture_output=True, text=True, timeout=3,
        )
        if win_id_result.returncode != 0:
            return "", ""
        win_id = win_id_result.stdout.strip()

        title_result = subprocess.run(
            ["xdotool", "getwindowname", win_id],
            capture_output=True, text=True, timeout=3,
        )
        title = title_result.stdout.strip()

        pid_result = subprocess.run(
            ["xdotool", "getwindowpid", win_id],
            capture_output=True, text=True, timeout=3,
        )
        pid = pid_result.stdout.strip()

        process_name = ""
        if pid:
            try:
                with open("/proc/" + pid + "/comm") as comm_file:
                    process_name = comm_file.read().strip()
            except Exception:
                pass

        return title, process_name
    except Exception:
        return "", ""


def get_active_window():
    # Returns (window_title, process_name) on any supported platform
    if platform.system() == "Windows":
        return get_active_window_windows()
    return get_active_window_linux()


def get_last_input_seconds_windows():
    # Returns seconds since last user input on Windows
    try:
        import ctypes
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(lii)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return millis / 1000.0
    except Exception:
        return 0.0


def get_last_input_seconds_linux():
    # Returns seconds since last input on Linux using xprintidle
    try:
        import subprocess
        result = subprocess.run(
            ["xprintidle"], capture_output=True, text=True, timeout=3
        )
        return int(result.stdout.strip()) / 1000.0
    except Exception:
        return 0.0


def get_idle_seconds():
    # Returns seconds since last user input on any supported platform
    if platform.system() == "Windows":
        return get_last_input_seconds_windows()
    return get_last_input_seconds_linux()


class IdentityHandler(BaseHTTPRequestHandler):
    # Tiny HTTP handler -- receives student identity from login app
    # CORS headers are required because welcome.html is served from
    # localhost:3000 (login_app) while this server runs on localhost:8091 --
    # different ports count as different origins to the browser
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        # Handles the CORS preflight request the browser sends before
        # the actual POST/DELETE when the request is cross-origin
        if self.path == "/identity":
            self.send_response(200)
            self._send_cors_headers()
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        # POST /identity -- called by login app after successful login
        # Body: {"student_id": "...", "session_id": "..."}
        if self.path == "/identity":
            import json
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                student_id = data.get("student_id", "")
                session_id = data.get("session_id", "")
                if student_id and session_id:
                    set_student_identity(student_id, session_id)
                    print("IDENTITY POST RECEIVED: student_id=" + student_id + " session_id=" + session_id)
                    self.send_response(200)
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(b'{"ok":true}')
                    return
            except Exception:
                pass
        self.send_response(400)
        self._send_cors_headers()
        self.end_headers()

    def do_DELETE(self):
        # DELETE /identity -- called by login app on logout
        if self.path == "/identity":
            clear_student_identity()
            print("IDENTITY DELETE RECEIVED")
            self.send_response(200)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            return
        self.send_response(400)
        self._send_cors_headers()
        self.end_headers()

    def log_message(self, format_str, *args):
        # Suppress default request logging
        pass


def run_identity_server():
    # Runs the identity HTTP server in a background thread
    server = HTTPServer(("127.0.0.1", IDENTITY_API_PORT), IdentityHandler)
    server.serve_forever()


def monitor_loop(school_id, device_id, server_id, insert_event_fn):
    # Main monitoring loop -- checks active window and idle state every
    # CHECK_INTERVAL_SECONDS and emits xAPI events accordingly
    last_resource_id = None
    last_resource_name = None
    last_resource_type = None
    last_resource_open_time = None
    last_active_time = time.time()
    is_idle = False
    idle_start_time = None

    while True:
        student_id, session_id = get_student_identity()

        if not student_id:
            time.sleep(CHECK_INTERVAL_SECONDS)
            continue

        idle_seconds = get_idle_seconds()
        title, process_name = get_active_window()

        if idle_seconds < IDLE_THRESHOLD_SECONDS:
            last_active_time = time.time()

            if is_idle:
                # Idle ended -- emit idle-ended
                is_idle = False
                idle_duration = int(time.time() - idle_start_time) if idle_start_time else 0
                stmt = build_statement(
                    student_id=student_id,
                    verb_slug="idle-ended",
                    object_id=ACTIVITY_BASE + "/session/" + session_id,
                    object_name="Session",
                    object_type="session",
                    school_id=school_id,
                    device_id=device_id,
                    server_id=server_id,
                    result={"duration": "PT" + str(idle_duration) + "S"},
                    extra_context={"session_id": session_id},
                )
                insert_event_fn(stmt)
                idle_start_time = None

            # Determine resource type and ID from active window
            if title and process_name:
                if "chrome" in process_name.lower() or \
                   "firefox" in process_name.lower() or \
                   "msedge" in process_name.lower() or \
                   "safari" in process_name.lower():
                    resource_type = "site"
                    resource_id = (ACTIVITY_BASE + "/resource/site/" +
                                   title.replace(" ", "_")[:80])
                elif "epub" in process_name.lower() or \
                     "pdf" in process_name.lower() or \
                     "reader" in process_name.lower():
                    resource_type = "book"
                    resource_id = (ACTIVITY_BASE + "/resource/book/" +
                                   title.replace(" ", "_")[:80])
                else:
                    resource_type = "app"
                    resource_id = (ACTIVITY_BASE + "/resource/app/" +
                                   process_name.replace(" ", "_")[:80])

                if resource_id != last_resource_id:
                    # Resource changed -- emit closed for old, opened for new
                    if last_resource_id:
                        closed_duration = int(time.time() - last_resource_open_time) if last_resource_open_time else 0
                        stmt = build_statement(
                            student_id=student_id,
                            verb_slug=last_resource_type + "-closed",
                            object_id=last_resource_id,
                            object_name=last_resource_name or last_resource_id,
                            object_type="resource",
                            school_id=school_id,
                            device_id=device_id,
                            server_id=server_id,
                            result={"duration": "PT" + str(closed_duration) + "S"},
                            extra_context={"session_id": session_id},
                        )
                        insert_event_fn(stmt)

                    stmt = build_statement(
                        student_id=student_id,
                        verb_slug=resource_type + "-opened",
                        object_id=resource_id,
                        object_name=title[:200],
                        object_type="resource",
                        school_id=school_id,
                        device_id=device_id,
                        server_id=server_id,
                        extra_context={"session_id": session_id},
                    )
                    insert_event_fn(stmt)

                    last_resource_id = resource_id
                    last_resource_name = title[:200]
                    last_resource_type = resource_type
                    last_resource_open_time = time.time()

        else:
            # Idle threshold exceeded
            if not is_idle:
                is_idle = True
                idle_start_time = time.time()
                stmt = build_statement(
                    student_id=student_id,
                    verb_slug="idle-started",
                    object_id=ACTIVITY_BASE + "/session/" + session_id,
                    object_name="Session",
                    object_type="session",
                    school_id=school_id,
                    device_id=device_id,
                    server_id=server_id,
                    extra_context={"session_id": session_id},
                )
                insert_event_fn(stmt)

            # Auto-logout if idle too long
            if time.time() - last_active_time > AUTO_LOGOUT_SECONDS:
                clear_student_identity()
                last_resource_id = None
                last_resource_name = None
                last_resource_type = None
                last_resource_open_time = None
                is_idle = False

        time.sleep(CHECK_INTERVAL_SECONDS)


def start_tracker(school_id, device_id, server_id, insert_event_fn):
    # Starts the identity API server and the monitoring loop in
    # background threads -- called from device_agent.py run()
    identity_thread = threading.Thread(
        target=run_identity_server, daemon=True
    )
    identity_thread.start()

    monitor_thread = threading.Thread(
        target=monitor_loop,
        args=(school_id, device_id, server_id, insert_event_fn),
        daemon=True,
    )
    monitor_thread.start()
