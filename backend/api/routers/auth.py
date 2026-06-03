from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, status

from ..database import get_client
from ..schemas.auth import SignupRequest, LoginRequest, AuthResponse
from ..schemas.user import User, int_to_grade, VALID_INTERESTS
from .. import config

router = APIRouter()

_AUTH_HEADERS = {
    "apikey": config.SUPABASE_KEY,
    "Content-Type": "application/json",
}


def _build_user_from_profile(student_id: str, email: str, profile: dict, interests: list[str]) -> User:
    grade_str = profile.get("grade")
    grade_int = None
    if grade_str and grade_str != "전학년":
        try:
            grade_int = int(grade_str.replace("학년", ""))
        except ValueError:
            pass

    return User(
        student_id=student_id,
        email=email,
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


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest):
    invalid = [i for i in body.interests if i not in VALID_INTERESTS]
    if invalid:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 관심분야: {invalid}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{config.SUPABASE_URL}/auth/v1/signup",
            headers=_AUTH_HEADERS,
            json={"email": body.email, "password": body.password},
        )

    if resp.status_code not in (200, 201):
        detail = resp.json().get("msg") or resp.json().get("error_description") or "회원가입 실패"
        raise HTTPException(status_code=400, detail=detail)

    auth_data = resp.json()
    access_token = (auth_data.get("access_token") or "")

    db = get_client()
    db.table("user_account").upsert(
        {"student_id": body.student_id, "password_hash": "[SUPABASE_AUTH_MANAGED]"},
        on_conflict="student_id",
    ).execute()

    db.table("user_profile").upsert(
        {
            "student_id": body.student_id,
            "name": body.name,
            "college": body.college,
            "department": body.department,
            "grade": int_to_grade(body.grade),
            "student_type": "재학생",
            "campus": "춘천",
        },
        on_conflict="student_id",
    ).execute()

    if body.interests:
        db.table("user_interest").delete().eq("student_id", body.student_id).execute()
        db.table("user_interest").insert(
            [{"student_id": body.student_id, "interest_name": i} for i in body.interests]
        ).execute()

    profile_row = db.table("user_profile").select("*").eq("student_id", body.student_id).single().execute()
    user = _build_user_from_profile(body.student_id, body.email, profile_row.data or {}, body.interests)

    return AuthResponse(access_token=access_token, user=user)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{config.SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers=_AUTH_HEADERS,
            json={"email": body.email, "password": body.password},
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    auth_data = resp.json()
    access_token = auth_data["access_token"]
    email = auth_data.get("user", {}).get("email", body.email)
    student_id = email.split("@")[0]

    db = get_client()
    profile_resp = db.table("user_profile").select("*").eq("student_id", student_id).execute()
    profile = profile_resp.data[0] if profile_resp.data else {}

    interests_resp = db.table("user_interest").select("interest_name").eq("student_id", student_id).execute()
    interests = [r["interest_name"] for r in (interests_resp.data or [])]

    user = _build_user_from_profile(student_id, email, profile, interests)

    return AuthResponse(access_token=access_token, user=user)
