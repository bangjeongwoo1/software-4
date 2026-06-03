from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_client
from ..deps import get_current_user
from ..schemas.user import User, UserUpdateRequest, int_to_grade, VALID_INTERESTS
from .. import config

router = APIRouter()

_AUTH_HEADERS = {
    "apikey": config.SUPABASE_KEY,
    "Content-Type": "application/json",
}


def _load_user(student_id: str) -> User:
    db = get_client()
    profile_resp = db.table("user_profile").select("*").eq("student_id", student_id).execute()
    profile = profile_resp.data[0] if profile_resp.data else {}

    interests_resp = db.table("user_interest").select("interest_name").eq("student_id", student_id).execute()
    interests = [r["interest_name"] for r in (interests_resp.data or [])]

    account_resp = db.table("user_account").select("student_id").eq("student_id", student_id).execute()
    if not account_resp.data:
        # 이전에 가입 후 DB 적재가 누락되었거나 대시보드 직접 생성된 사용자 복구
        try:
            db.table("user_account").upsert(
                {"student_id": student_id, "password_hash": "[AUTO_CREATED]"},
                on_conflict="student_id",
            ).execute()
            db.table("user_profile").upsert(
                {
                    "student_id": student_id,
                    "name": "신규 사용자",
                    "college": "미지정",
                    "department": "미지정",
                    "grade": "1학년",
                    "student_type": "재학생",
                    "campus": "춘천",
                },
                on_conflict="student_id",
            ).execute()
        except Exception as e:
            # RLS(Row-Level Security) 보안 정책 등으로 인서트가 거부되는 경우 예외 처리
            print(f"⚠️ RLS 또는 DB 제약으로 인해 자동 복구가 건너뛰어졌습니다: {e}")
            
        profile = {
            "name": "신규 사용자",
            "college": "미지정",
            "department": "미지정",
            "grade": "1학년",
            "student_type": "재학생",
            "campus": "춘천",
        }
    
    grade_str = profile.get("grade")
    grade_int = None
    if grade_str and grade_str != "전학년":
        try:
            grade_int = int(grade_str.replace("학년", ""))
        except ValueError:
            pass

    return User(
        student_id=student_id,
        name=profile.get("name"),
        college=profile.get("college"),
        department=profile.get("department"),
        grade=grade_int,
        gpa_prev=profile.get("gpa_prev"),
        campus=profile.get("campus"),
        student_type=profile.get("student_type"),
        phone=profile.get("phone"),
        interests=interests,
    )


@router.get("/me", response_model=User)
def get_me(student_id: str = Depends(get_current_user)):
    return _load_user(student_id)


@router.put("/me", response_model=User)
async def update_me(body: UserUpdateRequest, student_id: str = Depends(get_current_user)):
    if body.interests is not None:
        invalid = [i for i in body.interests if i not in VALID_INTERESTS]
        if invalid:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 관심분야: {invalid}")

    db = get_client()

    profile_patch: dict = {}
    if body.name is not None:
        profile_patch["name"] = body.name
    if body.college is not None:
        profile_patch["college"] = body.college
    if body.department is not None:
        profile_patch["department"] = body.department
    if body.grade is not None:
        profile_patch["grade"] = int_to_grade(body.grade)
    if body.gpa_prev is not None:
        profile_patch["gpa_prev"] = body.gpa_prev
    if body.campus is not None:
        profile_patch["campus"] = body.campus
    if body.student_type is not None:
        profile_patch["student_type"] = body.student_type
    if body.phone is not None:
        profile_patch["phone"] = body.phone

    if profile_patch:
        profile_patch["student_id"] = student_id
        if "student_type" not in profile_patch or profile_patch["student_type"] is None:
            profile_patch["student_type"] = "재학생"
        if "campus" not in profile_patch or profile_patch["campus"] is None:
            profile_patch["campus"] = "춘천"
        db.table("user_profile").upsert(profile_patch, on_conflict="student_id").execute()

    if body.interests is not None:
        db.table("user_interest").delete().eq("student_id", student_id).execute()
        if body.interests:
            db.table("user_interest").insert(
                [{"student_id": student_id, "interest_name": i} for i in body.interests]
            ).execute()

    if body.new_password and body.current_password:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.put(
                f"{config.SUPABASE_URL}/auth/v1/user",
                headers={**_AUTH_HEADERS},
                json={"password": body.new_password},
            )
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="비밀번호 변경에 실패했습니다.")

    return _load_user(student_id)
