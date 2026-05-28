from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

VALID_INTERESTS = {"장학", "대회", "개발", "데이터", "AI", "창업", "어학", "근로", "학업"}

GradeStr = Literal["전학년", "1학년", "2학년", "3학년", "4학년", "5학년"]


def grade_to_int(grade_str: str | None) -> int | None:
    if not grade_str or grade_str == "전학년":
        return None
    try:
        return int(grade_str.replace("학년", ""))
    except ValueError:
        return None


def int_to_grade(n: int | None) -> str:
    if n is None:
        return "전학년"
    return f"{n}학년"


class User(BaseModel):
    student_id: str
    email: str | None = None
    name: str | None = None
    college: str | None = None
    department: str | None = None
    grade: int | None = None
    gpa_prev: float | None = None
    campus: str | None = None
    student_type: str | None = None
    phone: str | None = None
    interests: list[str] = []


class UserUpdateRequest(BaseModel):
    name: str | None = None
    college: str | None = None
    department: str | None = None
    grade: int | None = Field(default=None, ge=1, le=6)
    gpa_prev: float | None = Field(default=None, ge=0.0, le=4.5)
    campus: str | None = None
    student_type: str | None = None
    phone: str | None = None
    interests: list[str] | None = None
    current_password: str | None = None
    new_password: str | None = Field(default=None, min_length=8)
