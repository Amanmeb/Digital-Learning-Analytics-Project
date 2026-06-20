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

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: str

class LogoutDeviceRequest(BaseModel):
    refresh_token: str

class LogoutDeviceRequest(BaseModel):
    session_id: str

class RefreshRequest(BaseModel):
    refresh_token: str
    device_id: str | None = None
    device_name: str | None = None

    
