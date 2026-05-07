# ContestKorea Crawler

콘테스트코리아의 학문, 과학, IT 분야 대회 정보를 수집해 Supabase에 저장하는 크롤러입니다.

## Run

프로젝트 루트에서 패키지 모드로 실행합니다.

```powershell
cd C:\Users\ljs44\SoftwareProject\software-4
```

DB 저장 없이 파싱 결과 확인:

```powershell
python -m contest.contest_crawler --pages 1 --limit 3 --dry-run
```

Supabase에 실제 저장:

```powershell
python -m contest.contest_crawler --pages 1
```

여러 페이지 수집:

```powershell
python -m contest.contest_crawler --pages 5
```

요청 간격 조절:

```powershell
python -m contest.contest_crawler --pages 5 --sleep 1.0
```

## CLI Options

| Option | Values | Description |
| --- | --- | --- |
| `--pages` | integer | 수집할 목록 페이지 수 |
| `--limit` | integer | 최대 상세 처리 수 |
| `--dry-run` | flag | DB 저장 없이 파싱 결과 출력 |
| `--sleep` | float | 요청 사이 대기 시간. 기본 0.7초 |

## Collection Rules

- 대상 URL: `https://www.contestkorea.com/sub/list.php`
- 카테고리: 학문, 과학, IT (`Txt_bcode=030310001`)
- 지역 파라미터: `Txt_area[0]=31`, `Txt_area[1]=32`, `Txt_area[2]=33`
- 저장 상태:
  - `접수예정` -> `upcoming`
  - `접수중` -> `open`
  - `마감임박` -> `closing`
- 위 상태가 아닌 항목은 저장하지 않습니다.

목록 파서는 실제 카드 영역인 `.list_style_2 > ul > li`만 대상으로 삼습니다. 하단 인기 목록, 추천 목록, 사이드바 링크는 제외합니다.

## Stored Tables

- `contest`: 공통 부모 row. `detail_url` 기준 upsert
- `contest_detail_1`: 목록 카드의 제목, 주최, 대상, 접수/심사/발표일, D-day 저장
- `contest_detail_2`: 상세 페이지 정보 테이블과 세부요강 본문 저장

`detail_text`는 상세 페이지 전체 body가 아니라 세부요강 영역인 `.view_detail_area .txt` 중심으로 저장합니다. 공통 메뉴, 헤더, 푸터, 인기 목록, 추천 목록은 제외합니다.

## URL Handling

`contest_detail_2`에는 아래 URL을 저장합니다.

```text
homepage_url
application_url
```

첨부 문서 URL은 현재 contest 스키마에 저장하지 않습니다. 상세 본문에 있는 링크 텍스트와 정보 테이블의 링크만 저장합니다.

일부 대회는 정보 테이블의 접수 버튼 링크가 실제 접수처가 아닌 중간 페이지일 수 있습니다. 예를 들어 `https://opendid.org/hackathon/2026/join.php`는 상세 본문에 명시된 접수처 URL보다 부정확할 수 있어, 파서는 본문에 명시된 URL을 우선합니다.

예상 보정 결과:

```text
application_url:
https://opendid.org/hackathon/2026/?utm_source=contest...
```

## Files

```text
contest/
  contest_config.py     # URL, 검색 파라미터, .env 설정
  contest_crawler.py    # CLI, HTTP 요청, 전체 흐름
  contest_parser.py     # 목록/상세 HTML 파싱
  contest_db.py         # Supabase upsert
  README.md
```

## Verification SQL

상태별 저장 개수:

```sql
SELECT status, COUNT(*)
FROM contest
GROUP BY status;
```

상세 테이블 개수:

```sql
SELECT COUNT(*) FROM contest_detail_1;
SELECT COUNT(*) FROM contest_detail_2;
```

최근 저장 row 확인:

```sql
SELECT contest_id, source_type, title, detail_url, status, created_at
FROM contest
ORDER BY contest_id DESC
LIMIT 20;
```

opendid URL 보정 확인:

```sql
SELECT c.title, d.homepage_url, d.application_url
FROM contest c
JOIN contest_detail_2 d USING (contest_id)
WHERE d.application_url ILIKE '%opendid%';
```

세부요강에 공통 메뉴 텍스트가 섞였는지 확인:

```sql
SELECT contest_id, title
FROM contest c
JOIN contest_detail_2 d USING (contest_id)
WHERE d.detail_text LIKE '%콘코알림%'
   OR d.detail_text LIKE '%전체현황%'
   OR d.detail_text LIKE '%인기순위%'
   OR d.detail_text LIKE '%고객센터%';
```

결과가 없어야 정상입니다.
