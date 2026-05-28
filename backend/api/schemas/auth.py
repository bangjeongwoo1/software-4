from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field
from .user import User


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str
    student_id: str = Field(pattern=r"^\d{9}$")
    college: str
    department: str
    grade: int = Field(ge=1, le=6)
    interests: list[str] = []


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User
