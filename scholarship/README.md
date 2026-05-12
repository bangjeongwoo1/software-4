# Scholarship Crawler

강원대학교 맞춤장학과 장학공지를 수집해 Supabase에 저장하는 크롤러입니다. 프로젝트 루트에서 패키지 모드로 실행합니다.

```powershell
cd C:\Users\ljs44\SoftwareProject\software-4
python -m scholarship.crawler --source all --pages 1 --limit 3 --dry-run
```

## Files

```text
scholarship/
  __init__.py
  config.py      # .env 로드, 대상 URL, Supabase 설정
  crawler.py     # CLI, 목록/상세 요청 흐름
  parser.py      # HTML 파싱, URL/값 정규화
  db.py          # Supabase upsert
  README.md
```

## Run

맞춤장학만 수집:

```powershell
python -m scholarship.crawler --source customized --pages 50
```

장학공지까지만 수집:

```powershell
python -m scholarship.crawler --source notice --pages 50
```

둘 다 수집:

```powershell
python -m scholarship.crawler --source all --pages 50
```

DB 저장 없이 확인:

```powershell
python -m scholarship.crawler --source customized --pages 1 --limit 3 --dry-run
python -m scholarship.crawler --source notice --pages 1 --limit 3 --dry-run
```

## CLI Options

| Option | Values | Description |
| --- | --- | --- |
| `--source` | `customized`, `notice`, `all` | 수집할 출처 |
| `--pages` | integer | 목록 페이지 수 |
| `--limit` | integer | source별 최대 상세 처리 수 |
| `--dry-run` | flag | DB 저장 없이 파싱 결과 출력 |

## Stored Tables

```text
source_site
scholarship
customized_detail_1
customized_detail_2
notice_detail_1
notice_detail_2
notice_llm
```

`scholarship`은 공통 부모 테이블입니다. `source_type`으로 `customized`와 `notice`를 구분하고, `detail_url` 기준으로 중복 upsert합니다.

## Customized Scholarship

맞춤장학은 목록 POST 요청 후 같은 세션으로 상세 GET을 이어서 수집합니다.

- `customized_detail_1`: 목록 카드 수준의 제목, 장학구분, 장학성격, 개요 저장
- `customized_detail_2`: 상세 조건 저장
- 학년은 5학년 값이 있어도 추천/필터링 기준에 맞춰 최대 4학년으로 정규화
- 학자금지원구간은 `0~9구간`, `0~8구간`을 그대로 0부터 저장
- 계열은 인문/자연/공학/예체능 boolean 컬럼으로 저장
- 관련문서는 텍스트가 아니라 실제 첨부 문서 URL을 `related_document_url`에 저장

`related_document_url`은 여러 문서가 있으면 줄바꿈으로 이어서 저장합니다. PDF뿐 아니라 맞춤장학에 자주 나오는 HWP/HWPX/DOC/DOCX도 문서 URL로 저장합니다.

## Notice Scholarship

장학공지는 목록 GET 요청 후 상세 페이지에서 본문, 첨부파일, 이미지를 수집합니다.

- `notice_detail_1`: 목록 수준의 공지 여부, 캠퍼스, 제목, 작성자, 등록일, 조회수 저장
- `notice_detail_2`: 상세 제목, 작성자, 문의전화, 본문 텍스트, 첨부파일 URL, 이미지 URL 저장
- `attachment_file_url`: 여러 파일이면 줄바꿈으로 저장
- `attachment_file_type`: PDF/HWP 등 파일 타입 저장
- `image_file_url`: 본문 대표 이미지 URL 저장

강원대 파일 URL은 한글 파일명이 깨지지 않도록 query string을 percent-encoding 해서 저장합니다.

## Upsert

중복 실행해도 row가 중복 삽입되지 않습니다.

- `scholarship`: `detail_url` 기준 upsert
- detail tables: `scholarship_id` 기준 upsert

## Schema Notes

맞춤장학 관련문서 컬럼은 현재 아래 이름을 사용합니다.

```sql
related_document_url TEXT
```

기존 Supabase에 `related_document_text`가 남아 있다면 아래 SQL로 변경합니다.

```sql
ALTER TABLE public.customized_detail_2
DROP COLUMN IF EXISTS related_document_text;

ALTER TABLE public.customized_detail_2
ADD COLUMN IF NOT EXISTS related_document_url TEXT;

NOTIFY pgrst, 'reload schema';
```

데모 환경에서 전체 초기화가 가능하면 `sql/scholarship_schema.sql` 전체를 다시 적용해도 됩니다.

## Verification SQL

출처별 저장 개수:

```sql
SELECT source_type, COUNT(*)
FROM scholarship
GROUP BY source_type;
```

상세 테이블 개수:

```sql
SELECT COUNT(*) FROM customized_detail_2;
SELECT COUNT(*) FROM notice_detail_2;
```

맞춤장학 관련문서 URL 확인:

```sql
SELECT title, related_document_url
FROM customized_detail_2
WHERE related_document_url IS NOT NULL
LIMIT 20;
```

장학공지 첨부파일 확인:

```sql
SELECT title, attachment_file_url, attachment_file_type, image_file_url
FROM notice_detail_2
WHERE attachment_file_url IS NOT NULL
   OR image_file_url IS NOT NULL
LIMIT 20;
```
