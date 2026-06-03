from pydantic import BaseModel, Field, field_validator


class FactSessionIn(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)
    student_id: str = Field(..., min_length=1, max_length=50)
    school_id: str = Field(..., min_length=1, max_length=20)
    device_id: str = Field(..., min_length=1, max_length=50)
    platform_id: str = Field(..., min_length=1, max_length=20)
    date_id: int
    project_id: str = Field(..., min_length=1, max_length=20)
    session_duration_minutes: int = Field(..., ge=0)
    is_offline: bool = True

    @field_validator("date_id")
    @classmethod
    def validate_date_id(cls, v: int) -> int:
        s = str(v)
        if len(s) != 8:
            raise ValueError("date_id must be 8 digits in yyyymmdd format")
        year, month, day = int(s[:4]), int(s[4:6]), int(s[6:])
        if not (1900 <= year <= 2099 and 1 <= month <= 12 and 1 <= day <= 31):
            raise ValueError("date_id is out of valid range")
        return v
