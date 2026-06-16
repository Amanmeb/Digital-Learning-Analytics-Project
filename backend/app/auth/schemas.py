from typing import Optional

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "student"
    student_id: Optional[str] = None
    teacher_id: Optional[str] = None
