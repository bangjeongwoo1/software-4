"""scholarship/parser.py 의 HTML 기반 큰 함수들 추가 테스트.

기존 ``test_scholarship_parser.py`` 가 작은 helper 함수 위주였다면, 이 파일은
``parse_customized_detail`` / ``parse_notice_detail`` / ``extract_kv_fields`` /
``find_notice_list_table`` / ``extract_attachments`` /
``extract_customized_related_document_url`` / ``extract_notice_body_text`` /
``extract_title`` / ``extract_notice_meta`` / ``trim_notice_noise`` 같이
BeautifulSoup 기반인 함수들을 다룬다.

총 22개 케이스.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from scholarship.parser import (
    extract_attachments,
    extract_customized_related_document_url,
    extract_kv_fields,
    extract_notice_body_text,
    extract_notice_meta,
    extract_title,
    find_notice_list_table,
    parse_customized_detail,
    parse_notice_detail,
    trim_notice_noise,
)


DETAIL_URL = "https://www.kangwon.ac.kr/ko/extn/90/janghak/view.do?janghakSn=999"
NOTICE_URL = "https://www.kangwon.ac.kr/ko/bbs/750/view.do?pstSn=42"


# ---------------------------------------------------------------------------
# extract_kv_fields  (3 cases) — 세 가지 레이아웃 모두 커버
# ---------------------------------------------------------------------------
def test_extract_kv_fields_ans_field_layout():
    html = """
    <div class="ans-field">
      <div class="ans-field-label">장학명</div>
      <div class="ans-field-value">국가장학금</div>
    </div>
    <div class="ans-field">
      <div class="ans-field-label">학년</div>
      <div class="ans-field-value">1학년, 2학년</div>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    fields = extract_kv_fields(soup)
    assert fields["장학명"] == "국가장학금"
    assert fields["학년"] == "1학년, 2학년"


def test_extract_kv_fields_table_layout():
    html = """
    <table>
      <tr><th>장학명</th><td>교내장학</td></tr>
      <tr><th>장학금액</th><td>500000</td></tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    fields = extract_kv_fields(soup)
    assert fields["장학명"] == "교내장학"
    assert fields["장학금액"] == "500000"


def test_extract_kv_fields_dl_layout():
    html = """
    <dl>
      <dt>장학명</dt><dd>가정형편</dd>
      <dt>비고</dt><dd>없음</dd>
    </dl>
    """
    soup = BeautifulSoup(html, "html.parser")
    fields = extract_kv_fields(soup)
    assert fields["장학명"] == "가정형편"
    assert fields["비고"] == "없음"


# ---------------------------------------------------------------------------
# parse_customized_detail  (3 cases)
# ---------------------------------------------------------------------------
CUSTOMIZED_DETAIL_HTML = """
<html><body>
<table>
  <tr><th>장학명</th><td>국가장학금 I</td></tr>
  <tr><th>개요</th><td>저소득층 학생 지원</td></tr>
  <tr><th>캠퍼스</th><td>춘천</td></tr>
  <tr><th>장학구분</th><td>국가</td></tr>
  <tr><th>장학성격</th><td>등록금</td></tr>
  <tr><th>국적구분</th><td>대한민국</td></tr>
  <tr><th>학생구분</th><td>학부생</td></tr>
  <tr><th>학년</th><td>1학년, 2학년, 3학년, 4학년</td></tr>
  <tr><th>학자금지원구간</th><td>0구간 ~ 8구간</td></tr>
  <tr><th>수업연한구분</th><td>4년제</td></tr>
  <tr><th>학점(직전학기)</th><td>15.0</td></tr>
  <tr><th>평점(직전학기)</th><td>3.5</td></tr>
  <tr><th>총평점</th><td>3.8</td></tr>
  <tr><th>장학금액</th><td>학기당 250만원</td></tr>
  <tr><th>선발시기</th><td>매학기</td></tr>
  <tr><th>추천필요여부</th><td>필요</td></tr>
  <tr><th>선발방법</th><td>서류심사</td></tr>
  <tr><th>수혜자격</th><td>가구 8분위 이하</td></tr>
  <tr><th>제출방법</th><td>온라인 신청</td></tr>
  <tr><th>비고</th><td>중복수혜 가능</td></tr>
  <tr><th>계열구분</th><td>인문, 자연, 공학</td></tr>
</table>
</body></html>
"""


def test_parse_customized_detail_basic_fields():
    detail = parse_customized_detail(CUSTOMIZED_DETAIL_HTML, DETAIL_URL)
    assert detail["title"] == "국가장학금 I"
    assert detail["summary"] == "저소득층 학생 지원"
    assert detail["campus_text"] == "춘천"
    assert detail["scholarship_type"] == "국가"
    assert detail["benefit_type"] == "등록금"
    assert detail["amount_text"] == "학기당 250만원"
    assert detail["requires_recommendation"] is True
    assert detail["selection_method_text"] == "서류심사"
    assert detail["eligibility_text"] == "가구 8분위 이하"


def test_parse_customized_detail_parses_numbers_and_ranges():
    detail = parse_customized_detail(CUSTOMIZED_DETAIL_HTML, DETAIL_URL)
    assert detail["grade_min"] == 1
    assert detail["grade_max"] == 4
    assert detail["income_level_min"] == 0
    assert detail["income_level_max"] == 8
    assert detail["credit_prev_value"] == 15.0
    assert detail["gpa_prev_semester_value"] == 3.5
    assert detail["gpa_total_value"] == 3.8


def test_parse_customized_detail_department_flags():
    detail = parse_customized_detail(CUSTOMIZED_DETAIL_HTML, DETAIL_URL)
    assert detail["department_humanities"] is True
    assert detail["department_science"] is True
    assert detail["department_engineering"] is True
    assert detail["department_arts"] is None


def test_parse_customized_detail_falls_back_to_list_item():
    # detail 페이지에 필드가 없을 때 list_item 값으로 폴백
    html = "<html><body><div></div></body></html>"
    list_item = {
        "title": "리스트 장학명",
        "summary": "리스트 요약",
        "scholarship_type": "리스트 구분",
        "benefit_type": "리스트 성격",
    }
    detail = parse_customized_detail(html, DETAIL_URL, list_item)
    assert detail["title"] == "리스트 장학명"
    assert detail["summary"] == "리스트 요약"
    assert detail["scholarship_type"] == "리스트 구분"
    assert detail["benefit_type"] == "리스트 성격"


# ---------------------------------------------------------------------------
# parse_notice_detail  (3 cases)
# ---------------------------------------------------------------------------
NOTICE_DETAIL_HTML = """
<html><body>
<h1 class="title">2026 장학생 모집 안내</h1>
<div class="board-view">
  공지사항입니다. 신청 기간은 2026.06.01 ~ 2026.06.30 이며,
  문의 033-250-1234 로 연락 주시기 바랍니다. 자세한 사항은 첨부파일을 참고하세요.
</div>
<table>
  <tr><th>작성자</th><td>장학팀</td></tr>
  <tr><th>캠퍼스</th><td>춘천</td></tr>
</table>
<div class="attach">
  <a href="/file.pdf">안내문.pdf</a>
  <a href="/form.hwp">신청서.hwp</a>
</div>
<img src="/img/banner.png">
</body></html>
"""


def test_parse_notice_detail_extracts_title_and_body():
    detail = parse_notice_detail(NOTICE_DETAIL_HTML, NOTICE_URL)
    assert detail["title"] == "2026 장학생 모집 안내"
    assert "신청 기간" in detail["raw_text"]
    assert detail["author"] == "장학팀"
    assert detail["campus_text"] == "춘천"


def test_parse_notice_detail_extracts_phone_and_attachments():
    detail = parse_notice_detail(NOTICE_DETAIL_HTML, NOTICE_URL)
    assert detail["contact_phone"] == "033-250-1234"
    assert "안내문.pdf" not in (detail["attachment_file_url"] or "")  # URL 만 들어감
    assert "/file.pdf" in detail["attachment_file_url"]
    assert "/form.hwp" in detail["attachment_file_url"]
    assert "PDF" in detail["attachment_file_type"]
    assert "HWP" in detail["attachment_file_type"]
    assert detail["image_file_url"].endswith("/img/banner.png")


def test_parse_notice_detail_uses_list_item_for_missing():
    html = "<html><body></body></html>"
    list_item = {"title": "리스트 제목", "campus_text": "원주", "author": "리스트작성자"}
    detail = parse_notice_detail(html, NOTICE_URL, list_item)
    assert detail["title"] == "리스트 제목"
    assert detail["campus_text"] == "원주"
    assert detail["author"] == "리스트작성자"


# ---------------------------------------------------------------------------
# find_notice_list_table  (2 cases)
# ---------------------------------------------------------------------------
def test_find_notice_list_table_finds_correct_table():
    html = """
    <table><tr><th>검색조건</th></tr></table>
    <table>
      <tr><th>번호</th><th>캠퍼스</th><th>제목</th><th>작성자</th><th>등록일시</th><th>조회수</th></tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    table = find_notice_list_table(soup)
    assert table is not None
    headers = {th.get_text(strip=True) for th in table.find_all("th")}
    assert "조회수" in headers


def test_find_notice_list_table_returns_none_when_missing():
    html = "<table><tr><th>x</th></tr></table>"
    soup = BeautifulSoup(html, "html.parser")
    assert find_notice_list_table(soup) is None


# ---------------------------------------------------------------------------
# extract_attachments  (3 cases)
# ---------------------------------------------------------------------------
def test_extract_attachments_filters_disallowed():
    html = """
    <a href="/a.pdf">안내</a>
    <a href="/b.docx">양식</a>
    <a href="/c.txt">텍스트</a>
    <a href="javascript:void(0)">자바스크립트</a>
    """
    soup = BeautifulSoup(html, "html.parser")
    result = extract_attachments(soup, "https://example.com/page")
    assert "https://example.com/a.pdf" in result["files"]
    assert "https://example.com/b.docx" in result["files"]
    assert all(".txt" not in url for url in result["files"])
    assert all("javascript" not in url for url in result["files"])


def test_extract_attachments_collects_images():
    html = '<img src="/img1.png"><img src="https://cdn.example.com/img2.jpg">'
    soup = BeautifulSoup(html, "html.parser")
    result = extract_attachments(soup, "https://example.com/page")
    assert "https://example.com/img1.png" in result["images"]
    assert "https://cdn.example.com/img2.jpg" in result["images"]


def test_extract_attachments_empty_html():
    soup = BeautifulSoup("", "html.parser")
    result = extract_attachments(soup, "https://example.com/page")
    assert result == {"files": [], "images": []}


# ---------------------------------------------------------------------------
# extract_customized_related_document_url  (2 cases)
# ---------------------------------------------------------------------------
def test_extract_customized_related_document_url_from_label_field():
    html = """
    <table>
      <tr><th>관련문서</th><td>
        <a href="/doc/guide.pdf">가이드</a>
        <a href="/doc/form.hwp">신청서</a>
      </td></tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    urls = extract_customized_related_document_url(soup, "https://example.com/x")
    assert "https://example.com/doc/guide.pdf" in urls
    assert "https://example.com/doc/form.hwp" in urls


def test_extract_customized_related_document_url_none_when_missing():
    html = "<table><tr><th>장학명</th><td>x</td></tr></table>"
    soup = BeautifulSoup(html, "html.parser")
    assert extract_customized_related_document_url(soup, "https://example.com") is None


# ---------------------------------------------------------------------------
# extract_notice_body_text  (2 cases)
# ---------------------------------------------------------------------------
def test_extract_notice_body_text_uses_selector():
    html = """
    <html><body>
    <div class="board-view">실제 본문은 여기에 충분히 길게 들어가야 의미가 있음</div>
    <script>removeme</script>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    text = extract_notice_body_text(soup)
    assert "실제 본문" in text
    assert "removeme" not in text


def test_extract_notice_body_text_falls_back_to_body():
    html = "<html><body>본문이 그냥 body 안에 있는 경우 입니다 길이가 충분합니다</body></html>"
    soup = BeautifulSoup(html, "html.parser")
    text = extract_notice_body_text(soup)
    assert "body 안에" in text


# ---------------------------------------------------------------------------
# extract_title  (2 cases)
# ---------------------------------------------------------------------------
def test_extract_title_from_h1():
    html = "<html><body><h1 class='title'>제목입니다</h1></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    assert extract_title(soup) == "제목입니다"


def test_extract_title_from_og_meta():
    html = "<html><head><meta property='og:title' content='OG 제목'></head></html>"
    soup = BeautifulSoup(html, "html.parser")
    assert extract_title(soup) == "OG 제목"


# ---------------------------------------------------------------------------
# extract_notice_meta  (1 case)
# ---------------------------------------------------------------------------
def test_extract_notice_meta_picks_author_and_campus():
    html = """
    <table>
      <tr><th>작성자</th><td>장학팀</td></tr>
      <tr><th>캠퍼스</th><td>춘천</td></tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    meta = extract_notice_meta(soup)
    assert meta["author"] == "장학팀"
    assert meta["campus_text"] == "춘천"


# ---------------------------------------------------------------------------
# trim_notice_noise  (1 case)
# ---------------------------------------------------------------------------
def test_trim_notice_noise_trims_around_markers():
    text = "장학공지 상세 진짜 본문 내용 목록으로 돌아가기"
    trimmed = trim_notice_noise(text)
    assert trimmed == "진짜 본문 내용"
