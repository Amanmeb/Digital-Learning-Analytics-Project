from fastapi import FastAPI

from app.routers import ingest

app = FastAPI(title="CDLAID Ingestion API", version="0.1.0", docs_url="/api/docs")

app.include_router(ingest.router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
