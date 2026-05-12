# Kangwon Scholarship User Schema

강원대학교 장학금 추천 서비스의 **사용자(User) 관련 DB 스키마**입니다.
인증, 프로필, 관심분야, 대회 참여 이력을 관리합니다.

## 파일

sql/
└── user_schema.sql

# Kangwon Scholarship User Schema

강원대학교 장학금 추천 서비스의 **사용자(User) 관련 DB 스키마**입니다.
인증, 프로필, 관심분야, 대회 참여 이력을 관리합니다.

## 파일
sql/
└── user_schema.sql

## 실행 방법

Supabase SQL Editor에서 `user_schema.sql` 전체를 복사해 실행하세요.

- 재실행 가능 (`DROP ... IF EXISTS CASCADE` 포함)
- 단독 실행 가능 (다른 스키마 파일에 의존하지 않음)

## 테이블 구조

| 테이블 | 관계 | 설명 |
|--------|------|------|
| user_account | - | 사용자 인증 (학번 + 비밀번호 해시) |
| user_profile | 1:1 | 장학금 검색 조건 프로필 |
| user_interest | 1:N | 관심분야 태그 (다중 선택) |
| user_competition | 1:N | 대회 참여 이력 |

## 테이블 관계
user_account (학번 + 비밀번호)
│
├──1:1── user_profile      (캠퍼스, 국적, 학년, 학점 등 검색 조건)
├──1:N── user_interest     (관심분야 태그 - 다중 선택)
└──1:N── user_competition  (대회 참여 이력 - 여러 건)

모든 자식 테이블은 `user_account` 삭제 시 `ON DELETE CASCADE`로 함께 삭제됩니다.

## 주요 컬럼 제약

### user_account
- `student_id` (PK): 학번 (TEXT — 0으로 시작하는 학번 대비)
- `password_hash`: bcrypt 해시값 (60자 고정)

### user_profile
- `campus`: 춘천 / 삼척
- `scholarship_category`: 전체 / 국가 / 교내 / 교외
- `department_field`: 인문 / 자연 / 공학 / 예체능
- `scholarship_nature`: 등록금보조 / 생활비지원
- `nationality_type`: 내국인 / 외국인
- `student_type`: 신입생 / 재학생
- `grade`: 전학년 / 1~5학년
- `income_level`: 0-8구간 / 9구간 / 제한없음
- `credit_prev`: 직전학기 취득학점 (0 이상)
- `gpa_prev`: 직전학기 평점 (0.0 ~ 4.5, 4.5 만점 기준)

### user_interest
- `interest_name`: 장학 / 대회 / 개발 / 데이터 / AI / 창업 / 어학 / 근로 / 학업
- `(student_id, interest_name)` UNIQUE 제약 — 동일 관심분야 중복 방지

### user_competition
- `competition_name`: 대회명 (자유 입력)
- `participated_at`: 참여일 (DATE)
- `result`: 결과 (자유 입력 — 장려상, 수료, 대상 등)

## 백엔드 처리 사항

DB에서 처리하지 않고 백엔드에서 검증해야 하는 항목:

- **비밀번호 길이 검증**: 최소 8자, 최대 72자 (bcrypt 입력 한계)
- **비밀번호 해싱**: bcrypt로 해싱 후 `password_hash`에 저장 (평문 저장 금지)
- **비밀번호 정책**: 특수문자/숫자 포함 여부 등

## 인덱스

| 인덱스 | 대상 | 용도 |
|--------|------|------|
| idx_user_interest_student_id | user_interest(student_id) | 학생별 관심분야 조회 |
| idx_user_competition_student_id | user_competition(student_id) | 학생별 대회이력 조회 |
| idx_user_competition_participated_at | user_competition(participated_at DESC) | 최근 대회 정렬 |

## 트리거

`updated_at` 자동 갱신을 위한 트리거가 다음 테이블에 적용됩니다.

- `user_account`
- `user_profile`
- `user_competition`

> `user_interest`는 INSERT/DELETE만 발생하므로 `updated_at` 컬럼과 트리거가 없습니다.

## 주의사항

- 재실행 시 기존 사용자 데이터 전부 삭제됨 (`DROP TABLE ... CASCADE`)
- 운영 DB에서 재실행 금지 — 개발/테스트 환경에서만 사용
- 함수명 `set_user_updated_at()`은 다른 스키마와 독립적으로 관리됨