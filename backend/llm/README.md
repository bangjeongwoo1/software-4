# LLM Notice Parser

장학 공지(`notice_detail_2`)의 비정형 데이터(본문 텍스트, 이미지, PDF)를 Gemini API로 분석해 구조화된 정보를 추출하고 `notice_llm` 테이블에 저장하는 모듈입니다. 프로젝트 루트에서 패키지 모드로 실행합니다.

```powershell
cd C:\Users\ljs44\SoftwareProject\software-4
python -m backend.llm.llm_runner --limit 3 --dry-run
```

## Files

```text
llm/
  __init__.py                    # from llm import run 지원
  llm_config.py                  # .env, Gemini 모델명, 프롬프트 파일 로드
  llm_client.py                  # Gemini 호출, 이미지/PDF 다운로드 및 bytes 전달
  llm_parser.py                  # JSON 파싱, 타입 변환, 항목별 검증
  llm_db.py                      # Supabase 처리 대상 조회 및 notice_llm upsert
  llm_runner.py                  # CLI 진입점
  prompts/
    notice_extraction.txt        # 장학 공지 구조화 추출 프롬프트
```

## Run

DB 저장 없이 Gemini 응답만 확인:

```powershell
python -m backend.llm.llm_runner --limit 1 --dry-run --sleep 0
```

미처리 공지 10건 저장:

```powershell
python -m backend.llm.llm_runner --limit 10
```

이미 처리된 공지도 다시 분석해서 갱신:

```powershell
python -m backend.llm.llm_runner --limit 10 --reprocess
```

전체 미처리 공지 처리:

```powershell
python -m backend.llm.llm_runner
```

## CLI Options

| Option | Values | Description |
| --- | --- | --- |
| `--limit` | integer | 처리할 공지 수. 전체 처리 시 생략 |
| `--dry-run` | flag | Gemini 호출과 파싱은 수행하지만 DB 저장은 skip |
| `--reprocess` | flag | 이미 `notice_llm`에 저장된 공지도 재처리 |
| `--sleep` | float | 공지 사이 대기 시간. 기본 4초 |
| `--retries` | integer | Gemini/API 호출 실패 시 공지별 재시도 횟수. 기본 2회 |
| `--retry-wait` | float | 재시도 전 기본 대기 시간. 재시도마다 배수로 증가 |

기본 실행은 `notice_llm`에 아직 없는 `scholarship_id`만 처리합니다. 기존 결과를 새로고침하려면 `--reprocess`를 붙입니다.

## Pipeline

```text
notice_detail_2 + notice_detail_1
        ↓
llm_db.fetch_notice_targets()
        ↓
raw_text, image_file_url, attachment_file_url 추출
        ↓
llm_client.download_asset()
        ↓
이미지/PDF bytes 생성
        ↓
Gemini API 호출
        ↓
llm_parser.parse_response()
        ↓
JSON 파싱 + 검증
        ↓
notice_llm UPSERT (scholarship_id 기준)
```

이미지와 PDF는 URL 문자열만 Gemini에 전달하지 않습니다. 코드가 먼저 `requests.get()`으로 파일을 다운로드한 뒤 bytes와 mime type을 Gemini에 직접 전달합니다.

## Stored Table

```sql
CREATE TABLE public.notice_llm (
    id BIGSERIAL PRIMARY KEY,
    scholarship_id BIGINT NOT NULL UNIQUE
        REFERENCES public.scholarship(scholarship_id) ON DELETE CASCADE,
    notice_title TEXT,
    summary TEXT,
    amount_text TEXT,
    department_text TEXT,
    grade_text TEXT,
    grade_min INT,
    grade_max INT,
    gpa_min DOUBLE PRECISION,
    application_start_date DATE,
    application_close_date DATE,
    parsed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

`scholarship_id` UNIQUE 제약으로 한 공지당 LLM 분석 결과가 하나만 저장됩니다. 중복 실행 시 새 row를 만들지 않고 기존 row를 갱신합니다.

## Source Data

`notice_detail_2`에서 아래 컬럼을 읽어 Gemini에 전달합니다.

| Column | 처리 방식 |
| --- | --- |
| `raw_text` | 텍스트로 직접 전달 |
| `image_file_url` | 이미지 다운로드 후 bytes 전달 |
| `attachment_file_url` | 줄바꿈 단위로 URL 분리 후 PDF만 다운로드해 bytes 전달 |

강원대 이미지 URL이 `application/octet-stream`으로 내려오는 경우가 있어, `llm_client.py`는 파일 시그니처와 URL의 `fn`, `dn` 파라미터를 함께 보고 PNG/JPEG/PDF mime type을 보정합니다. HWP 등 Gemini가 직접 처리하기 어려운 파일은 skip합니다.

## Prompt Engineering

장학 공지용 프롬프트는 `backend/llm/prompts/notice_extraction.txt`에서 관리합니다.

Gemini에는 다음 원칙을 지시합니다.

- JSON 객체 하나만 반환
- 추측 금지
- 문서에서 명확히 확인되는 값만 반환
- 없거나 애매하거나 충돌하는 값은 `null`
- 신청 기간은 `application_start_date`, `application_close_date`로 분리
- 날짜는 `YYYY-MM-DD` 형식만 허용
- 학기 이수 조건은 가능한 경우 학년 범위로 변환

프롬프트에서 1차로 제한하고, `llm_parser.py`에서 2차 검증합니다.

## Validation Rules

| Field | Rule | Invalid value |
| --- | --- | --- |
| `grade_min`, `grade_max` | 1~5 정수 | `null` |
| `재학생` | 학년 제한이 따로 없으면 1~4학년 전체로 정규화 | - |
| 학기 이수 조건 | `2학기 이상 이수` → 2~4학년, `4개 학기 이상 이수` → 3~4학년, `6개 학기 이상 이수` → 4학년 | 추론 불가 시 `null` |
| `grade_min > grade_max` | 자동 swap | 정상화 |
| `gpa_min` | 0.0~4.5 실수 | `null` |
| `application_start_date` | `YYYY-MM-DD` 형식 | `null` |
| `application_close_date` | `YYYY-MM-DD` 형식 | `null` |
| 빈 문자열 | 모든 TEXT 컬럼 | `null` |

Gemini가 예전 키인 `deadline`으로 응답하더라도 `llm_parser.py`에서 `application_close_date` fallback으로 읽습니다.
`재학생`처럼 명시 학년 제한이 없는 재학 조건은 학부 전체 대상인 1~4학년으로 정규화합니다.

## Environment

프로젝트 루트의 `.env` 또는 OS 환경변수에 아래 값이 필요합니다.

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.1-flash-lite-preview
LLM_DEFAULT_SLEEP=4
```

필요 패키지:

```text
google-genai
requests
supabase
python-dotenv
```

## Verification SQL

처리 진행률:

```sql
SELECT
    COUNT(*) AS total_notices,
    COUNT(nl.scholarship_id) AS parsed_count,
    COUNT(*) - COUNT(nl.scholarship_id) AS pending_count
FROM notice_detail_2 nd
LEFT JOIN notice_llm nl ON nd.scholarship_id = nl.scholarship_id;
```

최근 파싱 결과:

```sql
SELECT
    scholarship_id,
    notice_title,
    summary,
    amount_text,
    grade_min,
    grade_max,
    gpa_min,
    application_start_date,
    application_close_date,
    parsed_at
FROM notice_llm
ORDER BY parsed_at DESC
LIMIT 10;
```

신청 마감일이 남은 공지:

```sql
SELECT notice_title, application_start_date, application_close_date, amount_text
FROM notice_llm
WHERE application_close_date IS NOT NULL
  AND application_close_date >= CURRENT_DATE
ORDER BY application_close_date ASC
LIMIT 20;
```

학년/평점 필터링 예시:

```sql
SELECT notice_title, grade_text, gpa_min, application_close_date
FROM notice_llm
WHERE (grade_min IS NULL OR grade_min <= 3)
  AND (grade_max IS NULL OR grade_max >= 3)
  AND (gpa_min IS NULL OR gpa_min <= 3.3)
  AND application_close_date >= CURRENT_DATE
ORDER BY application_close_date ASC;
```

NULL 비율 확인:

```sql
SELECT
    ROUND(100.0 * COUNT(summary) / COUNT(*), 1) AS summary_pct,
    ROUND(100.0 * COUNT(amount_text) / COUNT(*), 1) AS amount_pct,
    ROUND(100.0 * COUNT(department_text) / COUNT(*), 1) AS department_pct,
    ROUND(100.0 * COUNT(grade_min) / COUNT(*), 1) AS grade_pct,
    ROUND(100.0 * COUNT(gpa_min) / COUNT(*), 1) AS gpa_pct,
    ROUND(100.0 * COUNT(application_start_date) / COUNT(*), 1) AS application_start_date_pct,
    ROUND(100.0 * COUNT(application_close_date) / COUNT(*), 1) AS application_close_date_pct
FROM notice_llm;
```

## Schema SQL

`notice_llm` 테이블은 `sql/scholarship_schema.sql`에 포함되어 있습니다. 데모 환경에서 전체 초기화할 경우 해당 SQL을 Supabase SQL Editor에 다시 적용한 뒤 장학 공지 크롤러와 LLM 파서를 순서대로 실행합니다.
