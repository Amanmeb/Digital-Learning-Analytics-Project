# CDLAID Ingestion API -- FastAPI entry point
# All routes are prefixed with /api/v1/
# Future versions use /api/v2/ -- existing agents continue on v1

import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.database import check_db_connection
from api.logger import logger
from api.routers import health, ingest
from api.routers.admin import (
    schools,
    regions,
    providers,
    projects,
    settings,
    notifications,
    import_data,
    templates as templates_router,
)

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
API_TITLE = "CDLAID Ingestion API"
API_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app):
    # Runs on startup -- checks database connection
    logger.info("Starting " + API_TITLE)
    if check_db_connection():
        logger.info("Database connection confirmed")
    else:
        logger.error("Database connection failed -- check DATABASE_URL")
    yield
    logger.info("Shutting down " + API_TITLE)


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs" if ENVIRONMENT == "development" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request, call_next):
    # Adds a unique request ID to every request and response
    # Format: REQ-YYYYMMDD-SCHOOLID-SEQUENCE
    school_id = request.headers.get("X-School-ID", "UNKNOWN")
    sequence = str(uuid.uuid4().int)[:4]
    from datetime import datetime
    date_str = datetime.utcnow().strftime("%Y%m%d")
    request_id = "REQ-" + date_str + "-" + school_id + "-" + sequence
    request.state.request_id = request_id

    start_time = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start_time) * 1000)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Duration-MS"] = str(duration_ms)
    return response


# Register all routers
app.include_router(health.router,               prefix="/api/v1")
app.include_router(ingest.router,               prefix="/api/v1")
app.include_router(schools.router,              prefix="/api/v1/admin")
app.include_router(regions.router,              prefix="/api/v1/admin")
app.include_router(providers.router,            prefix="/api/v1/admin")
app.include_router(projects.router,             prefix="/api/v1/admin")
app.include_router(settings.router,             prefix="/api/v1/admin")
app.include_router(notifications.router,        prefix="/api/v1/admin")
app.include_router(import_data.router,          prefix="/api/v1/admin")
app.include_router(templates_router.router,     prefix="/api/v1/admin")
