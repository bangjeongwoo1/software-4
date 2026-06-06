# Backend

강원대학교 장학 / 공모전 추천 서비스의 백엔드 구현부입니다.
크게 **데이터 수집 파이프라인**과 **FastAPI 서버** 두 축으로 구성됩니다.

```
Front (React) ──HTTP──> FastAPI (backend/api) ──supabase-py──> Supabase Postgres
                                                                       ▲
                                            크롤러 / LLM 파이프라인이 적재
```

---

## 디렉토리 구조

```
backend/
├── api/                  # FastAPI 서버 (Front ↔ DB 중계)
│   ├── main.py           # FastAPI app, CORS, 라우터 등록
│   ├── config.py         # SUPABASE_URL / SUPABASE_KEY 로드
│   ├── database.py       # supabase-py 클라이언트 싱글턴
│   ├── deps.py           # Supabase Auth API로 JWT 검증 → student_id 반환
│   ├── routers/
│   │   ├── auth.py            # POST /api/auth/signup, /login
│   │   ├── users.py           # GET, PUT /api/users/me
│   │   ├── scholarships.py    # GET /api/scholarships, /{id}
│   │   ├── contests.py        # GET /api/contests, /{id}
│   │   └── recommendations.py # GET /api/recommendations
│   └── schemas/
│       ├── auth.py
│       ├── user.py            # grade ↔ "N학년" 변환 포함
│       ├── scholarship.py
│       ├── contest.py
│       └── recommendation.py
│
├── scholarship/          # 장학 공지 크롤러
├── contest/              # 공모전 크롤러
└── llm/                  # 공지 본문 LLM 파싱 파이프라인
```

---

## 실행

```bash
# 1) Python 환경 (3.11 권장)
pip install -r requirements.txt

# 2) .env 준비 (.env.example 참고)
#    SUPABASE_URL, SUPABASE_KEY 필요

# 3) 서버 기동
uvicorn backend.api.main:app --reload --port 8000
# Swagger UI: http://localhost:8000/docs
```

---

## 아키텍처 핵심 결정

### 1. Front → FastAPI → DB 일방 흐름
프론트는 더 이상 Supabase에 직접 붙지 않습니다. 모든 데이터 접근은 FastAPI를 거치며,
API 스펙은 `docs/swagger.json` (v2.0.0) 기준입니다.

### 2. 인증: Supabase Auth REST API 프록시
- 가입/로그인: FastAPI가 `httpx`로 `/auth/v1/signup`, `/auth/v1/token` 호출
- 토큰 검증: `get_current_user`에서 `GET /auth/v1/user`로 토큰 확인 → email 앞부분을 `student_id`로 사용
- 로컬 `python-jose` 기반 검증을 쓰지 않는 이유: Supabase가 Legacy JWT secret을
  새 JWT Signing Keys 체계로 migration 했기 때문에, Auth API 위임 방식이 안정적

### 3. grade 표현 차이 흡수
- DB: `"3학년"` (TEXT)
- API: `3` (integer)
- `schemas/user.py`의 `grade_to_int` / `int_to_grade`가 양방향 변환

### 4. interests 검증
DB에 CHECK 제약이 있어 swagger의 자유 문자열을 그대로 받지 않고,
API 레이어에서 enum으로 좁힙니다.
```
["장학", "대회", "개발", "데이터", "AI", "창업", "어학", "근로", "학업"]
```

### 5. null = "조건 해당 없음" 정책
DB의 grade_min, grade_max, main_field 등에 null이 들어있으면
"모든 사용자 대상"으로 해석합니다. 즉 grade=3 으로 필터해도
grade_min/max가 둘 다 null인 행은 필터 통과 (포함).

### 6. JOIN 결과 컬럼 필터링은 Python 단에서
supabase-py 는 join된 자식 테이블 컬럼으로 `.eq()`/`.ilike()` 거는 걸 잘 지원하지 않습니다.
따라서:
- 부모(`scholarship.title`, `contest.title`)에 대한 keyword는 DB ILIKE
- 자식(grade, field 등)은 Python 사이드에서 후처리 필터

---

## 엔드포인트 구현 상태

| 영역 | 메서드 / 경로 | 상태 | 비고 |
|---|---|---|---|
| Auth | `POST /api/auth/signup` | ✅ | Supabase Auth → user_account/profile/interest insert |
| Auth | `POST /api/auth/login` | ✅ | Supabase Auth password grant 프록시 |
| Users | `GET /api/users/me` | ✅ | profile + interests join, grade 변환 |
| Users | `PUT /api/users/me` | ✅ | upsert + interests 재삽입, 비밀번호는 Auth PATCH |
| Scholarships | `GET /api/scholarships` | ✅ | keyword(ILIKE), grade, sort, 페이지네이션 |
| Scholarships | `GET /api/scholarships/{id}` | ✅ | 동일 JOIN + scholarship_id eq |
| Contests | `GET /api/contests` | ✅ | keyword, field, sort, 페이지네이션 |
| Contests | `GET /api/contests/{id}` | ✅ | 동일 JOIN + contest_id eq |
| Recommendations | `GET /api/recommendations` | ✅ | type=scholarship/contest, 점수 기반 정렬 |
| Notifications | — | ❌ | 이번 범위에서 제외 |

### 장학금 필터 동작 ([routers/scholarships.py](api/routers/scholarships.py))
- `keyword`: `scholarship.title ILIKE %keyword%`
- `grade` (1~4): `customized_detail_2.grade_min/max` 우선, 없으면 `notice_llm.grade_min/max`로 fallback.
  둘 다 null이면 "전 학년 대상"으로 간주 → 통과
- `sort`: `deadline_asc` / `deadline_desc` / `latest`
- swagger의 `category`, `department` 필터는 아직 미구현

### 공모전 필터 동작 ([routers/contests.py](api/routers/contests.py))
- `keyword`: `contest.title ILIKE`
- `field`: `contest_detail_2.main_field` 동등 비교. 크롤러가 실제로 적재하는 값은 `"학문•과학•IT"` 한 종류 위주
- `sort`: `deadline_asc` / `deadline_desc` / `latest`
- swagger의 `host_type` 필터는 아직 미구현

### 추천 점수 ([routers/recommendations.py](api/routers/recommendations.py))
프런트 Feed.jsx 로직을 백엔드로 이식:
- 학과 일치: +3
- 학년 해당: +2
- GPA 충족: +1
- 관심분야 일치 항목 1개당: +2

`match_score` 내림차순 정렬 후 `limit`개 반환. 각 항목에 매칭된 `reasons` 리스트 포함.

---

## DB 변경사항

- `sql/user_schema.sql` — user_profile에 `college TEXT` 컬럼 추가

---

## 알려진 한계 / TODO

- **누락 필터**: scholarships의 `category` / `department`, contests의 `host_type`
- **swagger 정렬 옵션 일부 미반영**: contests의 `prize_desc` (award_text 파싱 필요)
- **field 값 sync**: swagger enum이 실제 DB값(`학문•과학•IT`)과 불일치 — swagger 측 갱신 필요
- **추천 알고리즘**: 단순 가중합. 향후 사용자 클릭/지원 로그 기반 개인화 여지 있음
- **알림(notifications)** 미구현
