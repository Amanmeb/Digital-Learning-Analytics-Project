from fastapi import APIRouter

from app.schemas.offline_sync import (
    OfflineSyncRequest,
    OfflineSyncResponse,
)
from api.database import insert_offline_event

import json

router = APIRouter(
    prefix="/offline",
    tags=["Offline Sync"],
)


@router.post(
    "/sync",
    response_model=OfflineSyncResponse,
)
async def sync_events(payload: OfflineSyncRequest):

    accepted = 0
    duplicates = 0
    failed = 0

    for event in payload.events:

        try:

            inserted = insert_offline_event(
                fingerprint=event.fingerprint,
                school_id=payload.school_id,
                device_id=payload.device_id,
                statement=json.dumps(event.statement),
            )

            if inserted:
                accepted += 1
            else:
                duplicates += 1

        except Exception:
            failed += 1

    return OfflineSyncResponse(
        accepted=accepted,
        duplicates=duplicates,
        failed=failed,
    )