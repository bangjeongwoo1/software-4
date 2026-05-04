# Scholarship Crawler

강원대학교 장학 데이터를 Supabase에 저장하는 크롤러 모듈입니다. 프로젝트 루트에서 패키지 모드로 실행합니다.

```powershell
cd C:\Users\ljs44\SoftwareProject\software-4
python -m crawler.crawler --source all --pages 1 --limit 3 --dry-run
```

## Files

```text
crawler/
  crawler.py   # CLI 진입점, 목록/상세 요청 흐름 제어
  parser.py    # HTML 파싱, 값 정규화
  db.py        # Supabase 연결 및 upsert
  config.py    # .env 설정 로드
  .env         # Supabase URL/key 및 대상 URL
```

## Sources

맞춤장학만 크롤링:

```powershell
python -m crawler.crawler --source customized --pages 50
```

장학공지만 크롤링:

```powershell
python -m crawler.crawler --source notice --pages 50
```

둘 다 크롤링:

```powershell
python -m crawler.crawler --source all --pages 50
```

## Dry Run

DB 저장 없이 확인:

```powershell
python -m crawler.crawler --source customized --pages 1 --limit 3 --dry-run
python -m crawler.crawler --source notice --pages 1 --limit 3 --dry-run
```

## CLI Options

| Option | Values | Description |
| --- | --- | --- |
| `--source` | `customized`, `notice`, `all` | 수집할 출처 |
| `--pages` | integer | 목록 페이지 수 |
| `--limit` | integer | source별 최대 상세 페이지 수 |
| `--dry-run` | flag | DB 저장 없이 출력 |

## Stored Tables

```text
source_site
scholarship
customized_detail_1
customized_detail_2
notice_detail_1
notice_detail_2
```

`scholarship`은 공통 부모 테이블이고 `source_type`으로 `customized`와 `notice`를 구분합니다.

## Upsert

중복 실행해도 데이터가 중복 삽입되지 않습니다.

- `scholarship`: `detail_url` 기준 upsert
- detail tables: `scholarship_id` 기준 upsert

## Verification SQL

```sql
SELECT source_type, COUNT(*)
FROM scholarship
GROUP BY source_type;
```

```sql
SELECT COUNT(*) FROM customized_detail_2;
SELECT COUNT(*) FROM notice_detail_2;
```

```sql
SELECT title, attachment_file_url, attachment_file_type
FROM notice_detail_2
WHERE attachment_file_url IS NOT NULL;
```
