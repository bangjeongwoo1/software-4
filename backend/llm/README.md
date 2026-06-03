# LLM Parser

장학 공지(`notice`)와 공모전(`contest`)의 비정형 데이터를 Gemini API로 분석해 구조화된 정보를 추출하고 각각의 LLM 결과 테이블에 저장하는 모듈입니다. `--target` 옵션으로 처리 대상을 선택합니다.

```powershell
cd C:\Users\ljs44\SoftwareProject\software-4
python -m backend.llm.llm_runner --target notice --limit 3 --dry-run
python -m backend.llm.llm_runner --target contest --limit 3 --dry-run
```

## Files

```text
llm/
  __init__.py                    # from llm import run 지원
  llm_config.py                  # .env, Gemini 모델명, 프롬프트 파일 로드
  llm_client.py                  # Gemini 호출, 이미지/PDF 다운로드 및 bytes 전달
  llm_parser.py                  # JSON 파싱, 타입 변환, 항목별 검증
  llm_db.py                      # Supabase 처리 대상 조회 및 LLM 결과 upsert
  llm_runner.py                  # CLI 진입점
  prompts/
    notice_extraction.txt        # 장학 공지 구조화 추출 프롬프트
    contest_extraction.txt       # 공모전 요약 프롬프트
```

## Run

### notice

DB 저장 없이 Gemini 응답만 확인:

```powershell
python -m backend.llm.llm_runner --target notice --limit 1 --dry-run --sleep 0
```

미처리 공지 10건 저장:

```powershell
python -m backend.llm.llm_runner --target notice --limit 10
```

이미 처리된 공지도 다시 분석해서 갱신:

```powershell
python -m backend.llm.llm_runner --target notice --limit 10 --reprocess
```

### contest

DB 저장 없이 Gemini 응답만 확인:

```powershell
python -m backend.llm.llm_runner --target contest --limit 1 --dry-run --sleep 0
```

미처리 공모전 10건 저장:

```powershell
python -m backend.llm.llm_runner --target contest --limit 10
```

이미 처리된 공모전도 다시 분석해서 갱신:

```powershell
python -m backend.llm.llm_runner --target contest --limit 10 --reprocess
```

## CLI Options

| Option | Values | Description |
| --- | --- | --- |
| `--target` | `notice` \| `contest` | 처리 대상. 기본값 `notice` |
| `--limit` | integer | 처리할 항목 수. 전체 처리 시 생략 |
| `--dry-run` | flag | Gemini 호출과 파싱은 수행하지만 DB 저장은 skip |
| `--reprocess` | flag | 이미 결과 테이블에 저장된 항목도 재처리 |
| `--sleep` | float | 항목 사이 대기 시간. 기본 4초 |
| `--retries` | integer | Gemini/API 호출 실패 시 항목별 재시도 횟수. 기본 2회 |
| `--retry-wait` | float | 재시도 전 기본 대기 시간(초). 재시도마다 배수로 증가 |

기본 실행은 결과 테이블에 아직 없는 항목만 처리합니다. 기존 결과를 새로고침하려면 `--reprocess`를 붙입니다.

## Pipeline

### notice

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
Gemini API 호출 (notice_extraction.txt 프롬프트)
        ↓
llm_parser.parse_response(target="notice")
        ↓
JSON 파싱 + 검증
        ↓
notice_llm UPSERT (scholarship_id 기준)
```

### contest

```text
contest_detail_2 + contest
        ↓
llm_db.fetch_contest_targets()
        ↓
detail_text + 보조 컬럼(host_organization, target_text 등) 합산
        ↓
Gemini API 호출 (contest_summary.txt 프롬프트)
        ↓
llm_parser.parse_response(target="contest")
        ↓
JSON 파싱 + 검증
        ↓
contest_llm UPSERT (contest_id 기준)
```

notice는 이미지/PDF bytes를 Gemini에 직접 전달합니다. contest는 현재 텍스트만 처리하며, 나중에 첨부 URL이 수집되면 같은 asset 로직을 재사용할 수 있습니다.

## Stored Tables

### notice_llm

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

### contest_llm

```sql
CREATE TABLE public.contest_llm (
    id BIGSERIAL PRIMARY KEY,
    contest_id BIGINT NOT NULL UNIQUE
        REFERENCES public.contest(contest_id) ON DELETE CASCADE,
    contest_title TEXT,
    summary TEXT,
    parsed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

각 테이블의 ID 컬럼에 UNIQUE 제약이 있어 중복 실행 시 기존 row를 갱신합니다.

## Source Data

### notice

`notice_detail_2`에서 아래 컬럼을 읽어 Gemini에 전달합니다.

| Column | 처리 방식 |
| --- | --- |
| `raw_text` | 텍스트로 직접 전달 |
| `image_file_url` | 이미지 다운로드 후 bytes 전달 |
| `attachment_file_url` | 줄바꿈 단위로 URL 분리 후 PDF만 다운로드해 bytes 전달 |

강원대 이미지 URL이 `application/octet-stream`으로 내려오는 경우가 있어, `llm_client.py`는 파일 시그니처와 URL의 `fn`, `dn` 파라미터를 함께 보고 PNG/JPEG/PDF mime type을 보정합니다. HWP 등 Gemini가 직접 처리하기 어려운 파일은 skip합니다.

### contest

`contest_detail_2`에서 아래 컬럼을 합산해 하나의 텍스트로 Gemini에 전달합니다.

| Column | 역할 |
| --- | --- |
| `detail_text` | 상세 본문 (주요 LLM 입력) |
| `host_organization` | 주최/주관 |
| `main_field` | 분야 |
| `target_text` | 참가대상 |
| `reception_period_text` | 접수기간 |
| `award_text` | 시상내역 |
| `application_method` | 접수방법 |
| `homepage_url` | 홈페이지 |
| `application_url` | 접수 URL |

`contest` 테이블의 `title`도 함께 포함합니다.

## Prompt Engineering

### notice

`backend/llm/prompts/notice_extraction.txt`에서 관리합니다.

- JSON 객체 하나만 반환
- 추측 금지, 문서에서 명확히 확인되는 값만 반환
- 없거나 애매하거나 충돌하는 값은 `null`
- 신청 기간은 `application_start_date`, `application_close_date`로 분리
- 날짜는 `YYYY-MM-DD` 형식만 허용
- 학기 이수 조건은 가능한 경우 학년 범위로 변환

### contest

`backend/llm/prompts/contest_extraction.txt`에서 관리합니다.

- JSON 객체 하나만 반환, markdown 래핑 금지
- 추측 금지, 원문에 없는 내용은 작성 금지
- 한국어로 문단형 요약 작성
- 공모전명, 주최/주관, 분야, 참가대상, 접수기간, 심사/발표, 시상내역, 접수방법, URL, 유의사항 포함
- 날짜·금액·URL은 원문 그대로 보존
- 내용이 충분하지 않으면 `{"summary": null}` 반환

## Validation Rules

### notice

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

### contest

| Field | Rule |
| --- | --- |
| `summary` | 빈 문자열이면 `null`로 정규화 |
| 그 외 필드 | 저장하지 않음 |

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

### notice

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

### contest

처리 진행률:

```sql
SELECT
    COUNT(*) AS total_contests,
    COUNT(cl.contest_id) AS parsed_count,
    COUNT(*) - COUNT(cl.contest_id) AS pending_count
FROM contest_detail_2 cd
LEFT JOIN contest_llm cl ON cd.contest_id = cl.contest_id;
```

최근 요약 결과:

```sql
SELECT
    contest_id,
    contest_title,
    summary,
    parsed_at
FROM contest_llm
ORDER BY parsed_at DESC
LIMIT 20;
```

요약이 비어 있는 row 확인:

```sql
SELECT contest_id, contest_title, parsed_at
FROM contest_llm
WHERE summary IS NULL
ORDER BY parsed_at DESC;
```

원문 대비 확인:

```sql
SELECT
    c.contest_id,
    c.title,
    cd.detail_text,
    cl.summary
FROM contest c
JOIN contest_detail_2 cd ON c.contest_id = cd.contest_id
LEFT JOIN contest_llm cl ON c.contest_id = cl.contest_id
ORDER BY c.contest_id DESC
LIMIT 10;
```

## Schema SQL

`notice_llm`은 `sql/scholarship_schema.sql`, `contest_llm`은 `sql/contest_schema.sql`에 포함되어 있습니다. 처음부터 초기화할 경우 해당 SQL을 Supabase SQL Editor에 적용한 뒤 크롤러와 LLM 파서를 순서대로 실행합니다. 기존 데이터를 유지하면서 `contest_llm`만 추가하려면 해당 `CREATE TABLE` 문만 단독으로 실행합니다.
