"""HTML 파싱 함수들을 추가로 커버하는 contest_parser 테스트.

기존 ``test_contest_parser.py`` 가 작은 helper 함수 위주였다면, 이 파일은
``parse_contest_list`` / ``parse_contest_detail`` / ``parse_detail_table`` / ``parse_detail_text`` /
``find_list_cards`` / ``extract_card_*`` / ``extract_first_link`` / ``normalize_contest_urls`` 등
BeautifulSoup 기반 큰 함수들을 다룬다.

총 17개 케이스.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from contest.contest_parser import (
    extract_card_host,
    extract_card_target,
    extract_card_title,
    extract_first_link,
    extract_guideline_text,
    find_card_detail_link,
    find_list_cards,
    normalize_contest_urls,
    parse_contest_detail,
    parse_contest_list,
    parse_detail_table,
    parse_detail_text,
)


PAGE_URL = "https://www.contestkorea.com/sub/list.php?page=1"
DETAIL_URL = "https://www.contestkorea.com/sub/view.php?int_gbn=1&str_no=12345"


# ---------------------------------------------------------------------------
# 카드 한 개짜리 미니멀 list HTML 헬퍼
# ---------------------------------------------------------------------------
def _list_html(*, str_no: str = "12345", status_text: str = "접수중", title: str = "멋진 콘테스트") -> str:
    return f"""
    <div class="list_style_2">
      <ul>
        <li>
          <div class="title">
            <a href="/sub/view.php?int_gbn=1&str_no={str_no}">
              <span class="txt">{title}</span>
            </a>
          </div>
          <ul class="host">
            <li>주최: 회사A</li>
            <li>대상: 대학생</li>
          </ul>
          <div class="status">{status_text} D-7</div>
          <div class="dates">접수: 6.1 ~ 6.30 발표: 7.15</div>
        </li>
      </ul>
    </div>
    """


# ---------------------------------------------------------------------------
# parse_contest_list  (3 cases)
# ---------------------------------------------------------------------------
def test_parse_contest_list_extracts_card(frozen_today):
    items = parse_contest_list(_list_html(), PAGE_URL, year=2026)
    assert len(items) == 1
    item = items[0]
    assert item["str_no"] == "12345"
    assert item["title"] == "멋진 콘테스트"
    assert item["status"] == "open"
    assert item["status_text"] == "접수중"
    assert item["host"] == "회사A"
    assert item["target_text"] == "대학생"
    assert item["reception_start"] == "2026-06-01"
    assert item["reception_end"] == "2026-06-30"
    assert item["announcement_date"] == "2026-07-15"
    assert item["d_day"] == 7
    assert item["detail_url"] == DETAIL_URL


def test_parse_contest_list_skips_unknown_status(frozen_today):
    # STATUS_MAP 에 없는 상태 → 스킵
    items = parse_contest_list(_list_html(status_text="알수없음"), PAGE_URL, year=2026)
    assert items == []


def test_parse_contest_list_empty_when_no_cards(frozen_today):
    assert parse_contest_list("<html><body></body></html>", PAGE_URL, year=2026) == []


# ---------------------------------------------------------------------------
# find_list_cards / find_card_detail_link  (2 cases)
# ---------------------------------------------------------------------------
def test_find_list_cards_returns_only_first_level():
    soup = BeautifulSoup(_list_html(), "html.parser")
    cards = find_list_cards(soup)
    assert len(cards) == 1


def test_find_card_detail_link_returns_none_without_str_no():
    html = """
    <li>
      <div class="title">
        <a href="/sub/something.php">메뉴</a>
      </div>
    </li>
    """
    card = BeautifulSoup(html, "html.parser").find("li")
    assert find_card_detail_link(card) is None


# ---------------------------------------------------------------------------
# extract_card_title / host / target  (3 cases)
# ---------------------------------------------------------------------------
def test_extract_card_title_uses_txt_span():
    soup = BeautifulSoup(_list_html(title="제목XYZ"), "html.parser")
    card = soup.select_one("li")
    link = find_card_detail_link(card)
    assert extract_card_title(card, link) == "제목XYZ"


def test_extract_card_host_strips_label():
    soup = BeautifulSoup(_list_html(), "html.parser")
    card = soup.select_one("li")
    assert extract_card_host(card) == "회사A"


def test_extract_card_target_strips_label():
    soup = BeautifulSoup(_list_html(), "html.parser")
    card = soup.select_one("li")
    assert extract_card_target(card) == "대학생"


# ---------------------------------------------------------------------------
# parse_detail_table  (3 cases)
# ---------------------------------------------------------------------------
DETAIL_TABLE_HTML = """
<table>
  <tr><th>주최</th><td>회사A</td></tr>
  <tr><th>주관</th><td>기관B</td></tr>
  <tr><th>대표분야</th><td>IT</td></tr>
  <tr><th>참가대상</th><td>대학생</td></tr>
  <tr><th>접수기간</th><td>2026.06.01 ~ 2026.06.30</td></tr>
  <tr><th>심사기간</th><td>2026.07.01 ~ 2026.07.20</td></tr>
  <tr><th>대회지역</th><td>서울</td></tr>
  <tr><th>시상내역</th><td>대상 100만원</td></tr>
  <tr><th>접수방법</th><td>온라인</td></tr>
  <tr><th>참가비용</th><td>무료</td></tr>
  <tr><th>접수하기</th><td><a href="/sub/join.php?str_no=1">접수페이지</a></td></tr>
  <tr><th>홈페이지</th><td><a href="https://company-a.example.com">바로가기</a></td></tr>
</table>
"""


def test_parse_detail_table_extracts_labels():
    soup = BeautifulSoup(DETAIL_TABLE_HTML, "html.parser")
    result = parse_detail_table(soup, DETAIL_URL)
    assert result["main_field"] == "IT"
    assert result["target_text"] == "대학생"
    assert result["reception_period_text"] == "2026.06.01 ~ 2026.06.30"
    assert result["review_period_text"] == "2026.07.01 ~ 2026.07.20"
    assert result["contest_region"] == "서울"
    assert result["award_text"] == "대상 100만원"
    assert result["application_method"] == "온라인"
    assert result["participation_fee"] == "무료"


def test_parse_detail_table_concatenates_host_and_supervisor():
    # 주최/주관 이 둘 다 host_organization 으로 가는데, 두 번째는 " / " 로 이어붙임
    soup = BeautifulSoup(DETAIL_TABLE_HTML, "html.parser")
    result = parse_detail_table(soup, DETAIL_URL)
    assert result["host_organization"] == "회사A / 기관B"


def test_parse_detail_table_extracts_links():
    soup = BeautifulSoup(DETAIL_TABLE_HTML, "html.parser")
    result = parse_detail_table(soup, DETAIL_URL)
    assert result["application_url"].endswith("/sub/join.php?str_no=1")
    assert result["homepage_url"] == "https://company-a.example.com"


# ---------------------------------------------------------------------------
# parse_detail_text / extract_guideline_text  (2 cases)
# ---------------------------------------------------------------------------
def test_parse_detail_text_uses_guideline_area():
    html = """
    <div class="view_detail_area">
      <div class="txt">
        <p>지원자격: 누구나</p>
        <div class="attachments">첨부파일 영역 제외</div>
        <p>시상 내역: 상금 100만원</p>
      </div>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    text = parse_detail_text(soup)
    assert "지원자격" in text
    assert "시상" in text
    assert "첨부파일 영역" not in text


def test_extract_guideline_text_stops_at_h1_line():
    html = """
    <div>
      <p>첫째 줄</p>
      <h1 class="line">구분선</h1>
      <p>이건 안 나와야 함</p>
    </div>
    """
    container = BeautifulSoup(html, "html.parser").find("div")
    text = extract_guideline_text(container)
    assert "첫째 줄" in text
    assert "안 나와야 함" not in text


# ---------------------------------------------------------------------------
# extract_first_link  (2 cases)
# ---------------------------------------------------------------------------
def test_extract_first_link_resolves_relative():
    soup = BeautifulSoup('<td><a href="/page/x">바로가기</a></td>', "html.parser")
    cell = soup.find("td")
    assert extract_first_link(cell, "https://example.com/base/") == "https://example.com/page/x"


def test_extract_first_link_ignores_javascript_and_hash():
    soup = BeautifulSoup('<td><a href="javascript:void(0)">x</a></td>', "html.parser")
    cell = soup.find("td")
    assert extract_first_link(cell, "https://example.com") is None


# ---------------------------------------------------------------------------
# normalize_contest_urls  (2 cases)
# ---------------------------------------------------------------------------
def test_normalize_contest_urls_replaces_join_php():
    detail = {
        "detail_text": "공식 페이지: https://real-host.example.com/apply",
        "application_url": "https://www.contestkorea.com/sub/join.php?str_no=1",
        "homepage_url": None,
    }
    normalize_contest_urls(detail)
    assert detail["application_url"] == "https://real-host.example.com/apply"


def test_normalize_contest_urls_swaps_http_to_https_when_same_domain():
    detail = {
        "detail_text": "공식 https://example.com/page",
        "application_url": "https://example.com/page",  # join.php 아님
        "homepage_url": "http://example.com/old",  # http 라서 교체 대상
    }
    normalize_contest_urls(detail)
    assert detail["homepage_url"] == "https://example.com/page"


# ---------------------------------------------------------------------------
# parse_contest_detail (통합)  (1 case)
# ---------------------------------------------------------------------------
def test_parse_contest_detail_merges_table_and_text():
    html = f"""
    <html><body>
    {DETAIL_TABLE_HTML}
    <div class="view_detail_area">
      <div class="txt"><p>본문 내용입니다</p></div>
    </div>
    </body></html>
    """
    list_item = {"host": "리스트호스트", "target_text": "리스트대상"}
    result = parse_contest_detail(html, DETAIL_URL, list_item)
    # detail 에 host_organization 있으면 list_item 으로 덮어쓰지 않음
    assert result["host_organization"] == "회사A / 기관B"
    assert result["target_text"] == "대학생"
    assert "본문 내용입니다" in result["detail_text"]
