import hashlib
import json
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import XAPIStatementIn


def compute_fingerprint(statement: dict) -> str:
    """
    Stable SHA256 fingerprint used for idempotency.
    """
    canonical = json.dumps(statement, sort_keys=True, default=str)

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def normalize(statement: XAPIStatementIn) -> dict:
    """
    Pydantic v2 compatible conversion.
    """
    if hasattr(statement, "model_dump"):
        return statement.model_dump()

    return dict(statement)


# async def ingest_xapi_statement(
#     payload: XAPIStatementIn,
#     db: AsyncSession,
# ) -> dict:

async def ingest_xapi_statement(
        statement: XAPIStatementIn,
        db: AsyncSession,)-> dict:

    await db.execute(
        text("""
            INSERT INTO raw.xapi_statements (
                statement_id,
                actor,
                verb,
                object,
                raw_json
            )
            VALUES (
                :statement_id,
                :actor,
                :verb,
                :object,
                :raw_json
            )
        """),
        {
            "statement_id": statement.id,
            "actor": statement.actor.model_dump_json(),
            "verb": statement.verb.model_dump_json(),
            "object": statement.object.model_dump_json(),
            "raw_json": statement.model_dump_json(),
        },
    )

    await db.commit()

    return {
        "statement_id": statement.id
        # "statement_id": statement["statement_id"],
        # "fingerprint": fingerprint,
        # "status": "ingested_raw",
    }













