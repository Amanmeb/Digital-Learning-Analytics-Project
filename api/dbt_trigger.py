# dbt trigger service
# Runs dbt after successful sync with 5-minute cooldown
# Prevents back-to-back dbt runs when multiple schools sync simultaneously

import subprocess
import threading
import time
import os
from datetime import datetime, timezone
from api.logger import logger

DBT_COOLDOWN_SECONDS = 300
DBT_PROJECT_DIR = os.environ.get("DBT_PROJECT_DIR", "/app/cdlaid_dbt")
DBT_PROFILES_DIR = os.environ.get("DBT_PROFILES_DIR", "/app")

_last_dbt_run = 0
_dbt_lock = threading.Lock()
_dbt_scheduled = False


def _run_dbt():
    # Runs dbt in a subprocess and logs result
    global _last_dbt_run, _dbt_scheduled
    try:
        logger.info("dbt trigger: starting run")
        start = time.time()
        result = subprocess.run(
            ["dbt", "run",
             "--project-dir", DBT_PROJECT_DIR,
             "--profiles-dir", DBT_PROFILES_DIR],
            capture_output=True,
            text=True,
            timeout=600
        )
        duration = round(time.time() - start, 1)
        if result.returncode == 0:
            logger.info("dbt trigger: completed successfully in " + str(duration) + "s")
        else:
            logger.error("dbt trigger: failed after " + str(duration) + "s -- " + result.stderr[-500:])
    except subprocess.TimeoutExpired:
        logger.error("dbt trigger: timed out after 600 seconds")
    except Exception as e:
        logger.error("dbt trigger: error -- " + str(e))
    finally:
        _last_dbt_run = time.time()
        _dbt_scheduled = False


def trigger_dbt_if_ready():
    # Triggers dbt run if cooldown has passed
    # If cooldown not passed schedules a run for when it expires
    global _last_dbt_run, _dbt_scheduled
    now = time.time()
    with _dbt_lock:
        if _dbt_scheduled:
            return
        time_since_last = now - _last_dbt_run
        if time_since_last >= DBT_COOLDOWN_SECONDS:
            _dbt_scheduled = True
            thread = threading.Thread(target=_run_dbt, daemon=True)
            thread.start()
            logger.info("dbt trigger: queued immediately")
        else:
            wait_seconds = DBT_COOLDOWN_SECONDS - time_since_last
            _dbt_scheduled = True
            def delayed_run():
                time.sleep(wait_seconds)
                _run_dbt()
            thread = threading.Thread(target=delayed_run, daemon=True)
            thread.start()
            logger.info("dbt trigger: scheduled in " + str(round(wait_seconds)) + "s")