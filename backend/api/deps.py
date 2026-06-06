from __future__ import annotations

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from . import config

_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """Supabase Auth API로 토큰을 검증하고 student_id를 반환한다."""
    token = credentials.credentials

    resp = httpx.get(
        f"{config.SUPABASE_URL}/auth/v1/user",
        headers={
            "apikey": config.SUPABASE_KEY,
            "Authorization": f"Bearer {token}",
        },
        timeout=30.0,
    )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않거나 만료된 토큰입니다.",
        )

    email: str | None = resp.json().get("email")
    if not email or "@" not in email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰에서 사용자 정보를 찾을 수 없습니다.",
        )

    return email.split("@")[0]
