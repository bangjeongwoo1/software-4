from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..database import get_client
from ..deps import get_current_user
from ..schemas.recommendation import RecommendationItem, RecommendationResponse
from ..schemas.scholarship import ScholarshipSummary
from ..schemas.contest import ContestSummary
from .scholarships import _JOIN_SELECT as _S_SELECT, _normalize as _norm_s
from .contests import _JOIN_SELECT as _C_SELECT, _normalize as _norm_c

router = APIRouter()


def _score_scholarship(item: ScholarshipSummary, profile: dict, interests: list[str]) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    user_dept = profile.get("department", "")
    if user_dept and item.organization and user_dept in (item.organization or ""):
        score += 3
        reasons.append("학과 일치")

    user_grade_str = profile.get("grade", "")
    user_grade = None
    if user_grade_str and user_grade_str != "전학년":
        try:
            user_grade = int(user_grade_str.replace("학년", ""))
        except ValueError:
            pass

    if user_grade and item.target_grades:
        if user_grade in item.target_grades:
            score += 2
            reasons.append("학년 조건 충족")
    elif not item.target_grades:
        score += 1

    user_gpa = profile.get("gpa_prev")
    if user_gpa is not None and "장학" in interests:
        score += 2
        reasons.append("관심분야 일치 (장학)")

    return score, reasons


def _score_contest(item: ContestSummary, profile: dict, interests: list[str]) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    field = item.field or ""
    interest_map = {
        "IT": ["개발", "AI", "데이터"],
        "디자인": ["개발"],
        "창업": ["창업"],
        "마케팅": ["창업"],
        "학술": ["학업"],
    }
    matched_interests = interest_map.get(field, [])
    matched = [i for i in interests if i in matched_interests]
    if matched:
        score += len(matched) * 2
        reasons.append(f"관심분야 일치 ({', '.join(matched)})")

    if "대회" in interests:
        score += 2
        reasons.append("관심분야 일치 (대회)")

    return score, reasons


@router.get("", response_model=RecommendationResponse)
def get_recommendations(
    type: str = Query(..., enum=["scholarship", "contest"]),
    limit: int = Query(10, ge=1, le=50),
    student_id: str = Depends(get_current_user),
):
    db = get_client()

    profile_resp = db.table("user_profile").select("*").eq("student_id", student_id).execute()
    profile = profile_resp.data[0] if profile_resp.data else {}

    interests_resp = db.table("user_interest").select("interest_name").eq("student_id", student_id).execute()
    interests = [r["interest_name"] for r in (interests_resp.data or [])]

    results: list[RecommendationItem] = []

    if type == "scholarship":
        resp = db.table("scholarship").select(_S_SELECT).eq("status", "open").execute()
        for row in (resp.data or []):
            item = _norm_s(row)
            score, reasons = _score_scholarship(item, profile, interests)
            results.append(RecommendationItem(
                item_type="scholarship",
                scholarship=item,
                match_score=round(score / 10.0, 2),
                reasons=reasons,
            ))
    else:
        resp = db.table("contest").select(_C_SELECT).in_("status", ["open", "upcoming"]).execute()
        for row in (resp.data or []):
            item = _norm_c(row)
            score, reasons = _score_contest(item, profile, interests)
            results.append(RecommendationItem(
                item_type="contest",
                contest=item,
                match_score=round(score / 10.0, 2),
                reasons=reasons,
            ))

    results.sort(key=lambda x: x.match_score, reverse=True)
    return RecommendationResponse(type=type, items=results[:limit])
