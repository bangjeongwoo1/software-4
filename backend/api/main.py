from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, users, scholarships, contests, recommendations

app = FastAPI(
    title="Kangwon National University Scholarship & Contest Recommendation API",
    description="Front → FastAPI Back → DB 구조의 장학 및 공모전 추천 서비스 API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(scholarships.router, prefix="/api/scholarships", tags=["Scholarships"])
app.include_router(contests.router, prefix="/api/contests", tags=["Contests"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
