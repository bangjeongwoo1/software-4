# Scholarship & Career Information Recommender — Frontend

학교 홈페이지에 올라오는 장학금·취업·대회 공고를 학생 조건에 맞춰 추천해주는 시스템의 **프론트엔드 1차 골격**입니다.

> **Stack**: React 18 + Vite + React Router DOM v6
> **Theme**: 라이트 테마 (학교/공식 느낌)
> **Status**: 전체 페이지 골격 + 더미 데이터 단계

---

## 빠른 시작

### A. Docker 사용 (권장)

```bash
# 개발 모드 (HMR 지원, http://localhost:5173)
docker compose up --build

# 프로덕션 모드 (nginx 정적 호스팅, http://localhost:8080)
docker compose -f docker-compose.prod.yml up --build
```

종료: `Ctrl+C` 후 `docker compose down`

### B. 로컬 Node 사용

```bash
npm install
npm run dev          # http://localhost:5173
npm run build        # 프로덕션 빌드
npm run preview      # 빌드 결과 미리보기
```

---

## Docker 구성

| 파일 | 용도 |
| --- | --- |
| `Dockerfile.dev` | 개발용 — Node 20-alpine + Vite dev 서버 |
| `Dockerfile` | 프로덕션 — 멀티스테이지 빌드 + nginx-alpine |
| `nginx.conf` | SPA 라우팅 폴백(`try_files $uri /index.html`) + gzip + 정적 캐시 |
| `docker-compose.yml` | 개발 (포트 5173, 소스 bind mount, HMR) |
| `docker-compose.prod.yml` | 프로덕션 (포트 8080) |
| `.dockerignore` | node_modules, dist, .git 등 빌드 컨텍스트에서 제외 |

> 개발 모드는 `src/`, `index.html`, `vite.config.js`, `package.json`을 호스트에서 컨테이너로 bind mount 하므로 코드 수정이 즉시 반영됩니다. `node_modules`는 컨테이너 내부 것을 사용해 호스트와 충돌하지 않습니다.

---

## 페이지 구성 (사이트맵 매핑)

| 메뉴 | 라우트 | 파일 | 설명 |
| --- | --- | --- | --- |
| 로그인 | `/login` | `pages/Login.jsx` | 아이디·비밀번호·로그인 버튼 |
| 마이 페이지 | `/mypage` | `pages/MyPage.jsx` | 내 정보 기입(학과·학년·평점·관심분야), **대회 참여 이력** |
| 장학·대회 리스트 | `/list` | `pages/ItemList.jsx` | 학과 홈페이지·한국장학재단·교내·콘테스트 코리아 출처 필터 |
| 상세 정보 | `/detail/:id` | `pages/ItemDetail.jsx` | 장학·대회 페이지 외부 링크 연결 |
| 인기 장학·대회 | `/popular` | `pages/Popular.jsx` | 필터 기반 추천 (조회수 정렬) |
| 피드 | `/feed` | `pages/Feed.jsx` | 추천 기반 피드 / 조회수 기반 피드 탭 |
| 알림 | `/notifications` | `pages/Notifications.jsx` | 희망 수신 방식 설정·알림 목록 조회 |
| 알림 전송(관리자) | `/admin/notifications` | `pages/AdminNotifications.jsx` | 알림 작성·SMS 발송·이력 |

---

## 폴더 구조

```
software-4-frontend/
├── package.json
├── vite.config.js
├── index.html
├── Dockerfile                  # 프로덕션 (multi-stage + nginx)
├── Dockerfile.dev              # 개발 (vite dev 서버)
├── docker-compose.yml          # 개발 compose (default)
├── docker-compose.prod.yml     # 프로덕션 compose
├── nginx.conf                  # SPA 라우팅 nginx 설정
├── .dockerignore
├── .gitignore
├── README.md
└── src/
    ├── main.jsx               # 엔트리, BrowserRouter 마운트
    ├── App.jsx                # 라우트 정의
    ├── components/
    │   ├── Layout.jsx         # 헤더 + 사이드바 + Outlet
    │   └── ItemCard.jsx       # 공고 카드
    ├── pages/
    │   ├── Login.jsx
    │   ├── MyPage.jsx
    │   ├── ItemList.jsx
    │   ├── ItemDetail.jsx
    │   ├── Popular.jsx
    │   ├── Feed.jsx
    │   ├── Notifications.jsx
    │   └── AdminNotifications.jsx
    ├── data/
    │   ├── items.js           # 장학·대회 더미 (10건)
    │   ├── user.js            # 로그인 사용자 더미
    │   └── notifications.js   # 알림 더미
    └── styles/
        └── global.css         # 디자인 토큰 + 컴포넌트 스타일
```

---

## 추천 점수(피드) 로직 (더미)

`src/pages/Feed.jsx` 의 `recommendScore`:

- 학과 일치(또는 '전체') **+3**
- 학년 해당 **+2**
- 평점 충족 **+1**
- 관심 분야 매치 항목당 **+2**

점수 내림차순 상위 8건 노출. 추후 백엔드 추천 API로 교체.

---

## 다음 단계 제안

1. **백엔드 연동**: `src/data/*.js`를 fetch 기반 API 호출로 교체
2. **인증**: `/login` 더미 → 실제 학사 SSO/JWT 연동
3. **상태 관리**: 전역 상태(예: 로그인 사용자)는 Zustand/Context 도입
4. **공지 크롤링**: 4개 출처(학과/한국장학재단/교내/콘테스트 코리아) 수집 파이프라인
5. **테스트**: Vitest + React Testing Library

---

## 라이선스 / 출처

학교 캡스톤·소프트웨어 프로젝트 용도. 외부 사이트(한국장학재단, 콘테스트 코리아)는 각 사이트의 약관을 따릅니다.
