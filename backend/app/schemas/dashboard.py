from typing import Any

from pydantic import BaseModel


class DashboardCards(BaseModel):
    sessions: int | None = None
    learning_minutes: int | None = None
    assignments_completed: int | None = None
    average_score: float | None = None

    students: int | None = None
    teachers: int | None = None
    schools: int | None = None
    devices: int | None = None

class DashboardSummaryResponse(BaseModel):
    scope: str
    cards: DashboardCards
    charts: list[Any]
    recent_activity: list[Any]