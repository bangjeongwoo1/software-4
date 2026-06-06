"""Unit tests for ``backend/scholarship/parser.py``.

총 65개 케이스 — pytest --collect-only 로 정확한 수 확인 가능.
"""

from __future__ import annotations

import datetime

import pytest

from scholarship.parser import (
    attachment_types,
    build_status,
    clean_text,
    extract_period,
    extract_phone,
    find_campus,
    find_view_count,
    first_value,
    format_date,
    infer_attachment_ext,
    normalize_asset_url,
    normalize_campus_text,
    normalize_detail_url,
    normalize_optional_text,
    parse_customized_list,
    parse_department_flags,
    parse_grade_range,
    parse_income_range,
    parse_int,
    parse_iso_date,
    parse_notice_list,
    parse_number,
    parse_recommendation,
    pick,
    unique,
)


@pytest.mark.parametrize(
    "given, expected",
    [
        (None, ""),
        ("", ""),
        ("  hello   world\t\n", "hello world"),
    ],
)
def test_clean_text_basic(given, expected):
    assert clean_text(given) == expected


def test_clean_text_removes_icon_noise():
    assert clean_text("chevron_forward 다음 keyboard_arrow_down") == "다음"


@pytest.mark.parametrize(
    "given, expected",
    [
        (None, "all"),
        ("", "all"),
        ("ALL", "all"),
        ("전체", "all"),
        ("기타", "all"),
    ],
)
def test_normalize_campus_text_defaults(given, expected):
    assert normalize_campus_text(given) == expected


def test_normalize_campus_text_single():
    assert normalize_campus_text("춘천") == "춘천"


def test_normalize_campus_text_multiple_preserves_order():
    assert normalize_campus_text("춘천, 삼척") == "춘천,삼척"
    assert normalize_campus_text("도계 / 삼척") == "삼척,도계"


@pytest.mark.parametrize(
    "given, expected",
    [
        ("1학년", (1, 1)),
        ("1학년, 2학년, 3학년, 4학년", (1, 4)),
        ("전체", (None, None)),
        ("제한없음", (None, None)),
        (None, (None, None)),
    ],
)
def test_parse_grade_range(given, expected):
    assert parse_grade_range(given) == expected


@pytest.mark.parametrize(
    "given, expected",
    [
        (None, (None, None)),
        ("전체", (None, None)),
        ("3구간", (3, 3)),
    ],
)
def test_parse_income_range_simple(given, expected):
    assert parse_income_range(given) == expected


@pytest.mark.parametrize(
    "given, expected",
    [
        (None, None),
        ("", None),
        ("-", False),
        ("Y", True),
    ],
)
def test_parse_recommendation(given, expected):
    assert parse_recommendation(given) == expected


@pytest.mark.parametrize(
    "given, expected",
    [
        (None, None),
        ("abc", None),
        ("score 85.5", 85.5),
    ],
)
def test_parse_number(given, expected):
    assert parse_number(given) == expected


@pytest.mark.parametrize(
    "given, expected",
    [
        (None, None),
        ("1,234", 1234),
        ("none", None),
    ],
)
def test_parse_int(given, expected):
    assert parse_int(given) == expected


def test_build_status_open_when_no_dates(frozen_today):
    assert build_status(None, None) == "open"


def test_build_status_upcoming(frozen_today):
    assert build_status("2027-01-01", "2027-12-31") == "upcoming"


def test_build_status_closed(frozen_today):
    assert build_status("2020-01-01", "2020-12-31") == "closed"


def test_build_status_in_range_is_open(frozen_today):
    assert build_status("2020-01-01", "2030-12-31") == "open"


def test_extract_period_full_range():
    assert extract_period("2024.01.01 ~ 2024.12.31") == ("2024-01-01", "2024-12-31")


def test_extract_period_same_year_short_end():
    assert extract_period("2024.01.05 ~ 12.31") == ("2024-01-05", "2024-12-31")


def test_extract_period_single_date():
    assert extract_period("접수: 2024.05.20") == ("2024-05-20", None)


def test_extract_period_returns_none_for_empty():
    assert extract_period(None) == (None, None)
    assert extract_period("") == (None, None)


def test_parse_department_flags_none():
    assert parse_department_flags(None) == {
        "department_humanities": None,
        "department_science": None,
        "department_engineering": None,
        "department_arts": None,
    }


def test_parse_department_flags_engineering_only():
    flags = parse_department_flags("공학계열")
    assert flags["department_engineering"] is True
    assert flags["department_humanities"] is None
    assert flags["department_science"] is None
    assert flags["department_arts"] is None


def test_parse_department_flags_multiple():
    flags = parse_department_flags("인문, 자연, 예체능")
    assert flags == {
        "department_humanities": True,
        "department_science": True,
        "department_engineering": None,
        "department_arts": True,
    }


def test_normalize_detail_url_keeps_only_janghakSn():
    given = "https://www.kangwon.ac.kr/ko/extn/90/janghak/view.do?janghakSn=999&extra=ignored"
    assert normalize_detail_url(given) == (
        "https://www.kangwon.ac.kr/ko/extn/90/janghak/view.do?janghakSn=999"
    )


def test_normalize_detail_url_keeps_only_pstSn():
    given = "https://www.kangwon.ac.kr/ko/bbs/750/view.do?pstSn=42&pageIndex=1"
    assert normalize_detail_url(given) == (
        "https://www.kangwon.ac.kr/ko/bbs/750/view.do?pstSn=42"
    )


def test_format_date_valid():
    assert format_date("2024", "5", "20") == "2024-05-20"


def test_format_date_invalid_month():
    assert format_date("2024", "13", "1") is None


def test_parse_iso_date_none():
    assert parse_iso_date(None) is None


def test_parse_iso_date_valid():
    assert parse_iso_date("2024-05-20") == datetime.date(2024, 5, 20)


def test_parse_iso_date_invalid():
    assert parse_iso_date("not-a-date") is None


def test_extract_phone_with_label():
    assert extract_phone("문의 010-1234-5678") == "010-1234-5678"


def test_extract_phone_landline():
    assert extract_phone("전화 033-250-1234") == "033-250-1234"


def test_extract_phone_none_when_missing():
    assert extract_phone("아무 번호도 없습니다") is None


def test_infer_attachment_ext_from_path():
    assert infer_attachment_ext("https://example.com/notice/file.pdf") == "pdf"


def test_infer_attachment_ext_from_query_filename():
    url = "https://example.com/download?fileName=test.docx"
    assert infer_attachment_ext(url) == "docx"


def test_infer_attachment_ext_from_link_text():
    assert infer_attachment_ext("https://example.com/down", "[양식.hwp]") == "hwp"


def test_normalize_asset_url_encodes_korean_query():
    encoded = normalize_asset_url("https://example.com/path?fn=한글.hwp")
    assert encoded == "https://example.com/path?fn=%ED%95%9C%EA%B8%80.hwp"


def test_unique_preserves_order_and_dedups():
    assert unique(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


def test_unique_empty():
    assert unique([]) == []


def test_pick_returns_first_present_label():
    fields = {"개요": "내용 A", "장학명": "이름"}
    assert pick(fields, "장학명", "개요") == "이름"


def test_pick_returns_none_when_missing():
    assert pick({"x": "y"}, "a", "b") is None


def test_first_value_empty():
    assert first_value([]) is None


def test_first_value_non_empty():
    assert first_value(["x", "y"]) == "x"


def test_attachment_types_filters_disallowed():
    urls = [
        "https://example.com/file.pdf",
        "https://example.com/doc.docx",
        "https://example.com/img.png",
    ]
    assert attachment_types(urls) == ["PDF", "DOCX"]


def test_attachment_types_empty():
    assert attachment_types([]) == []


def test_find_campus_picks_known_keyword():
    assert find_campus(["서울", "춘천 캠퍼스"]) == "춘천 캠퍼스"


def test_find_campus_none_when_no_keyword():
    assert find_campus(["서울", "부산"]) is None


def test_find_view_count_returns_first_numeric_from_end():
    assert find_view_count(["title", "춘천", "123"]) == 123


def test_find_view_count_none_when_no_digits():
    assert find_view_count(["abc", "def"]) is None


def test_normalize_optional_text_returns_none_for_blank():
    assert normalize_optional_text("   ") is None
    assert normalize_optional_text(None) is None


def test_normalize_optional_text_keeps_content():
    assert normalize_optional_text("  hello  ") == "hello"


def test_parse_customized_list_extracts_row():
    html = """
    <table>
      <tr>
        <td>1</td>
        <td>장학금A</td>
        <td>국가</td>
        <td>등록금</td>
        <td>요약 A</td>
        <td><a href="/ko/extn/90/janghak/view.do?janghakSn=100">상세</a></td>
      </tr>
    </table>
    """
    items = parse_customized_list(html, "https://www.kangwon.ac.kr/ko/extn/90/janghak/list.do")
    assert len(items) == 1
    item = items[0]
    assert item["title"] == "장학금A"
    assert item["scholarship_type"] == "국가"
    assert item["benefit_type"] == "등록금"
    assert item["summary"] == "요약 A"
    assert item["detail_url"].endswith("janghakSn=100")


def test_parse_notice_list_extracts_row():
    html = """
    <table>
      <tr><th>번호</th><th>캠퍼스</th><th>제목</th><th>작성자</th><th>등록일시</th><th>조회수</th></tr>
      <tr>
        <td>공지</td>
        <td>춘천</td>
        <td><a href="/ko/bbs/750/view.do?pstSn=42">학생 장학 안내</a></td>
        <td>장학팀</td>
        <td>2026-06-05</td>
        <td>123</td>
      </tr>
    </table>
    """
    items = parse_notice_list(html, "https://www.kangwon.ac.kr/ko/bbs/750/list.do")
    assert len(items) == 1
    item = items[0]
    assert item["is_notice"] is True
    assert item["campus_text"] == "춘천"
    assert item["title"] == "학생 장학 안내"
    assert item["author"] == "장학팀"
    assert item["registered_at"] == "2026-06-05"
    assert item["view_count"] == 123
    assert item["detail_url"].endswith("pstSn=42")
