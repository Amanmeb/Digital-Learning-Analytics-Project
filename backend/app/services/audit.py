import json
from uuid import uuid4

from sqlalchemy import text


async def log_event(
    db,
    user_id,
    event,
    ip_address=None,
    user_agent=None,
    device_id=None,
    metadata=None,
):
    await db.execute(
        text("""
            INSERT INTO auth.audit_logs (
                id,
                user_id,
                event,
                ip_address,
                user_agent,
                device_id,
                metadata,
                created_at
            )
            VALUES (
                :id,
                :user_id,
                :event,
                :ip_address,
                :user_agent,
                :device_id,
                CAST(:metadata AS jsonb),
                NOW()
            )
        """),
        {
            "id": str(uuid4()),
            "user_id": user_id,
            "event": event,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "device_id": device_id,
            "metadata": json.dumps(metadata or {}),
        },
    )