from __future__ import annotations

from pydantic import BaseModel
from .scholarship import ScholarshipSummary
from .contest import ContestSummary


class RecommendationItem(BaseModel):
    item_type: str  # "scholarship" | "contest"
    scholarship: ScholarshipSummary | None = None
    contest: ContestSummary | None = None
    match_score: float
    reasons: list[str] = []


class RecommendationResponse(BaseModel):
    type: str
    items: list[RecommendationItem]
