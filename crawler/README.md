# Scholarship Crawler

강원대학교 장학금 공지와 장학금 조회 페이지를 크롤링해서 MySQL에 저장하는 모듈입니다. 목록 페이지에서 상세 링크를 수집하고, 상세 페이지에서 제목, 기관, 금액, 신청 기간, 지원 자격, 학년, 평점, 이수학점, 소득구간 등의 조건을 추출합니다.

## Files

```text
crawler/
  crawler.py   # 실행 진입점, 목록/상세 페이지 수집, DB 저장 흐름 제어
  parser.py    # HTML 파싱, 장학금 필드와 조건 추출
  db.py        # MySQL 연결, 장학금 upsert 저장
  config.py    # 환경 변수 기반 설정
```

관련 SQL 파일은 `sql/` 폴더에 있습니다.

```text
sql/init.sql                 # 처음 DB를 만들 때 사용
sql/migrate_conditions.sql   # 기존 DB에 조건 컬럼/테이블을 추가할 때 사용
```

## Setup

필요 패키지를 설치합니다.

```bash
pip install -r requirements.txt
```

처음 실행하는 DB라면 테이블을 생성합니다.

```powershell
Get-Content sql/init.sql | mysql -u root -p
```

`mysql` 명령어가 PATH에 없다면 MySQL Workbench에서 `sql/init.sql` 내용을 실행해도 됩니다.

## Environment Variables

PowerShell 예시입니다.

```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="3306"
$env:DB_USER="root"
$env:DB_PASSWORD="your_password"
$env:DB_NAME="scholarship_db"
$env:SCHOLARSHIP_LIST_URL="https://www.kangwon.ac.kr/ko/bbs/750/list.do"
```

주요 환경 변수:

| Name | Default | Description |
| --- | --- | --- |
| `SCHOLARSHIP_LIST_URL` | empty | 장학금 목록 URL |
| `CRAWLER_REQUEST_TIMEOUT` | `10` | HTTP 요청 제한 시간 |
| `CRAWLER_USER_AGENT` | `Mozilla/5.0 (compatible; ScholarshipCrawler/1.0)` | 요청 User-Agent |
| `LIST_LINK_SELECTOR` | `a` | 일반 게시판 상세 링크 CSS selector |
| `TITLE_SELECTOR` | `h1, h2, .title, .view-title` | 제목 CSS selector |
| `CONTENT_SELECTOR` | `article, .content, .view-content, body` | 본문 CSS selector |
| `DB_HOST` | `localhost` | MySQL host |
| `DB_PORT` | `3306` | MySQL port |
| `DB_USER` | `root` | MySQL user |
| `DB_PASSWORD` | empty | MySQL password |
| `DB_NAME` | `scholarship_db` | MySQL database |

## Run

환경 변수 `SCHOLARSHIP_LIST_URL`을 설정했다면:

```bash
python -m crawler.crawler
```

목록 URL을 직접 넘길 수도 있습니다.

```bash
python crawler/crawler.py --list-url "https://www.kangwon.ac.kr/ko/bbs/750/list.do" --pages 10
```

일부 상세 페이지만 테스트하려면 `--limit`을 같이 사용합니다.

```bash
python crawler/crawler.py --list-url "https://www.kangwon.ac.kr/ko/bbs/750/list.do" --pages 10 --limit 20
```

강원대학교 맞춤형 장학 조회 페이지도 지원합니다.

```bash
python crawler/crawler.py --list-url "https://www.kangwon.ac.kr/ko/extn/90/janghak/list.do" --pages 5
```

## Stored Data

기본 장학금 정보는 `scholarship` 테이블에 저장됩니다.

- `title`
- `organization`
- `scholarship_type`
- `benefit_type`
- `amount_text`
- `campus_text`
- `apply_start_date`
- `apply_end_date`
- `eligibility_text`
- `selection_criteria_text`
- `application_method_text`
- `detail_url`
- `source_site`
- `status`

추천/검색에 쓰기 좋은 조건 정보는 `scholarship_condition` 테이블에 저장됩니다.

- `grade_min`, `grade_max`
- `gpa_min`
- `credit_min`
- `income_level_min`, `income_level_max`
- `is_new_student`
- `is_enrolled_student`
- `is_transfer_student`
- `is_foreign_student`
- `department_text`
- `raw_condition_text`

같은 `detail_url`이 이미 있으면 새로 추가하지 않고 기존 데이터를 업데이트합니다.

## Reset Crawled Data

테이블 구조는 유지하고 크롤링 데이터만 지우려면 MySQL에서 아래 SQL을 실행합니다.

```sql
SET FOREIGN_KEY_CHECKS=0;
TRUNCATE TABLE scholarship_condition;
TRUNCATE TABLE scholarship;
SET FOREIGN_KEY_CHECKS=1;
```
