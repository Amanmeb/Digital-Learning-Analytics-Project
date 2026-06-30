# app/schemas/api_response.py

from typing import Any, Optional

from pydantic import BaseModel


class ApiResponse(BaseModel):
    status: str
    message: str
    data: Optional[Any] = None