from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel


class OfflineEvent(BaseModel):
    fingerprint: str
    statement: Dict[str, Any]
    created_at: datetime

class OfflineSyncRequest(BaseModel):
    device_id: str
    school_id: str
    events: List[OfflineEvent]

class OfflineSyncResponse(BaseModel):
    accepted: int
    duplicates: int
    failed: int