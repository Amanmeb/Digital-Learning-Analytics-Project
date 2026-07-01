from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.ingest import router as ingest_router

app = FastAPI(
    title="CDLAID Ingestion API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url=None,
)

app.include_router(ingest_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"service": "Digital Learning Analytics API"}


@app.get("/health")
async def health():
    return {"status": "ok"}

# @app.get("/")
# async def root() -> dict:
#     return {
#         "service": "cdlaid-ingestion-api",
#         "status": "running",
#         "version": "0.1.0"
#     }


# @app.get("/health")
# async def health() -> dict:
#     return {"status": "ok"}

 
