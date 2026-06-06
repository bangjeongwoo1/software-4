from __future__ import annotations

from pydantic import BaseModel


class ScholarshipSummary(BaseModel):
    id: int
    title: str | None = None
    summary: str | None = None
    campus: str | None = None
    organization: str | None = None
    category: str | None = None
    amount: str | None = None
    deadline: str | None = None
    d_day: int | None = None
    status: str | None = None
    source_type: str | None = None
    target_grades: list[int] = []
    detail_url: str | None = None


class ScholarshipDetail(ScholarshipSummary):
    summary: str | None = None
    eligibility: str | None = None
    application_method: str | None = None
    application_url: str | None = None
    application_start: str | None = None
    application_end: str | None = None
    contact: str | None = None
    campus_text: str | None = None
    department_text: str | None = None
    grade_text: str | None = None
    gpa_min: float | None = None
    raw: dict | None = None


class ScholarshipListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[ScholarshipSummary]
