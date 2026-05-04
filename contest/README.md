# ContestKorea Crawler

콘테스트코리아의 학문, 과학, IT 분야 대회 정보를 수집해 Supabase에 저장하는 크롤러입니다.

## 실행

프로젝트 루트에서 패키지 모드로 실행합니다.

```powershell
cd C:\Users\ljs44\working\crawler
```

DB 저장 없이 파싱 결과만 확인:

```powershell
python -m contest.contest_crawler --pages 1 --limit 3 --dry-run
```

Supabase에 실제 저장:

```powershell
python -m contest.contest_crawler --pages 1
```

page 1 전체 저장 대상만 확인하려면 현재 기준 9개입니다.

```powershell
python -m contest.contest_crawler --pages 1 --limit 9 --dry-run
```

## 수집 조건

- 대상 URL: `https://www.contestkorea.com/sub/list.php`
- 카테고리: 학문, 과학, IT (`Txt_bcode=030310001`)
- 대상: 대학생, 대학원생, 일반인
- 지역 파라미터: `Txt_area[0]=31`, `Txt_area[1]=32`, `Txt_area[2]=33`
- 저장 상태:
  - `접수예정` -> `upcoming`
  - `접수중` -> `open`
  - `마감임박` -> `closing`
- 위 상태가 아닌 항목은 DB에 저장하지 않습니다.

목록 파서는 실제 카드 영역인 `.list_style_2 > ul > li`만 대상으로 삼습니다. 하단 인기 목록, 추천 목록, 사이드바의 `view.php?str_no=...` 링크는 저장 대상에서 제외합니다.

## 저장 데이터

- `contest`: 공통 부모 row입니다. `detail_url` 기준으로 upsert합니다.
- `contest_detail_1`: 목록 카드에서 보이는 제목, 주최, 대상, 접수/심사/발표일, D-day를 저장합니다.
- `contest_detail_2`: 상세 페이지의 정보 테이블과 세부요강 본문을 저장합니다.

`detail_text`는 상세 페이지 전체 body가 아니라 세부요강 영역인 `.view_detail_area .txt`만 저장합니다. 공통 메뉴, 헤더, 푸터, 인기 목록, 추천 목록은 제외합니다.

컬럼은 대부분 NULL을 허용합니다. 다만 값이 실제로 파싱되면 빈 문자열이 아니라 실제 값으로 저장하고, 빈 문자열이나 공백 문자열은 `NULL`로 정리합니다.

## Status CHECK

Supabase의 `contest.status` CHECK 제약은 반드시 영어 코드값이어야 합니다.

```sql
ALTER TABLE public.contest
DROP CONSTRAINT IF EXISTS contest_status_check;

ALTER TABLE public.contest
ADD CONSTRAINT contest_status_check
CHECK (status IN ('upcoming', 'open', 'closing'));
```

확인:

```sql
SELECT
  conname,
  pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'public.contest'::regclass
  AND conname = 'contest_status_check';
```

결과에 `'open '`처럼 따옴표 안 공백이 들어가면 안 됩니다. 정확히 `'open'`이어야 합니다.

## 파일

```text
contest/
  __init__.py          # from contest import run 지원
  contest_config.py    # URL, 파라미터, .env 설정
  contest_crawler.py   # CLI, HTTP 요청, 전체 흐름
  contest_parser.py    # 목록/상세 HTML 파싱
  contest_db.py        # Supabase upsert
  README.md
```

`contest___init__.py`는 오타 파일로 보이며 실행에는 사용하지 않습니다.

## 검증 SQL

```sql
SELECT status, COUNT(*)
FROM contest
GROUP BY status;
```

```sql
SELECT COUNT(*) FROM contest_detail_1;
SELECT COUNT(*) FROM contest_detail_2;
```

최근 저장된 row 확인:

```sql
SELECT contest_id, source_type, title, detail_url, status, created_at
FROM contest
ORDER BY contest_id DESC
LIMIT 20;
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
