from __future__ import annotations

from pydantic import BaseModel


class ContestSummary(BaseModel):
    id: int
    title: str | None = None
    host: str | None = None
    target: str | None = None
    host_type: str | None = None
    field: str | None = None
    prize: str | None = None
    deadline: str | None = None
    d_day: int | None = None
    status: str | None = None
    detail_url: str | None = None
    tags: list[str] = []


class ContestDetail(ContestSummary):
    description: str | None = None
    eligibility: str | None = None
    target_text: str | None = None
    reception_period_text: str | None = None
    review_period_text: str | None = None
    contest_region: str | None = None
    application_method: str | None = None
    application_url: str | None = None
    participation_fee: str | None = None
    reception_start: str | None = None
    reception_end: str | None = None
    announcement_date: str | None = None
    raw: dict | None = None


class ContestListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[ContestSummary]
