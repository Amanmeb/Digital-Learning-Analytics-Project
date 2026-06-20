# app/schemas/api_response.py

from pydantic import BaseModel
from typing import Any, Optional


class ApiResponse(BaseModel):
    status: str
    message: str
    data: Optional[Any] = None