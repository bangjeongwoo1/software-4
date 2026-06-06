"""Unit tests for ``backend/contest/contest_parser.py``.

총 38개 케이스.
"""

from __future__ import annotations

import datetime

import pytest

from contest.contest_parser import (
    calc_d_day,
    clean_label_noise,
    clean_multiline_text,
    clean_text,
    extract_d_day,
    extract_labeled_value,
    extract_status,
    extract_status_text,
    extract_str_no,
    extract_title_from_text,
    extract_urls_from_text,
    find_same_domain_url,
    format_date,
    normalize_detail_url,
    parse_date_range,
    parse_labeled_date_range,
    parse_labeled_single_date,
    parse_month_day,
    should_replace_application_url,
    unique_by_detail_url,
    unique_strings,
)


@pytest.mark.parametrize(
    "given, expected",
    [
        (None, ""),
        ("", ""),
        ("  hello   world  ", "hello world"),
    ],
)
def test_clean_text(given, expected):
    assert clean_text(given) == expected


def test_clean_multiline_text_strips_blank_lines():
    assert clean_multiline_text("a\n\nb\nc") == "a\nb\nc"


def test_clean_multiline_text_empty():
    assert clean_multiline_text(None) == ""


def test_format_date_none():
    assert format_date(None) is None


def test_format_date_with_date():
    assert format_date(datetime.date(2024, 5, 20)) == "2024-05-20"


def test_extract_str_no_present():
    assert extract_str_no("/sub/view.php?int_gbn=1&str_no=12345") == "12345"


def test_extract_str_no_empty_value():
    assert extract_str_no("/sub/view.php?str_no=") is None


def test_extract_str_no_missing():
    assert extract_str_no("/sub/view.php?int_gbn=1") is None


def test_normalize_detail_url_canonical_form():
    given = "/sub/view.php?int_gbn=1&str_no=42&extra=x"
    assert normalize_detail_url(given) == (
        "https://www.contestkorea.com/sub/view.php?int_gbn=1&str_no=42"
    )


def test_normalize_detail_url_no_str_no_returns_absolute():
    result = normalize_detail_url("/page", "https://example.com/base/")
    assert result == "https://example.com/page"


def test_parse_month_day_valid():
    assert parse_month_day("6.5", 2026) == datetime.date(2026, 6, 5)


def test_parse_month_day_invalid_month():
    assert parse_month_day("13.1", 2026) is None


def test_parse_month_day_no_match():
    assert parse_month_day("abc", 2026) is None


def test_parse_date_range_same_year():
    assert parse_date_range("6.1 ~ 6.30", 2026) == ("2026-06-01", "2026-06-30")


def test_parse_date_range_crosses_year():
    assert parse_date_range("12.20 ~ 1.10", 2026) == ("2026-12-20", "2027-01-10")


def test_parse_labeled_date_range_matches_label():
    text = "접수: 6.1 ~ 6.30 심사: 7.1 ~ 7.20"
    assert parse_labeled_date_range(text, "접수", 2026) == ("2026-06-01", "2026-06-30")


def test_parse_labeled_date_range_no_label():
    assert parse_labeled_date_range("발표: 7.15", "접수", 2026) == (None, None)


def test_parse_labeled_single_date_matches():
    assert parse_labeled_single_date("발표: 7.15", "발표", 2026) == "2026-07-15"


def test_parse_labeled_single_date_missing():
    assert parse_labeled_single_date("접수: 6.1 ~ 6.30", "발표", 2026) is None


def test_calc_d_day_future(frozen_today):
    assert calc_d_day("2026-06-10") == 5


def test_calc_d_day_today(frozen_today):
    assert calc_d_day("2026-06-05") == 0


def test_calc_d_day_invalid(frozen_today):
    assert calc_d_day(None) is None
    assert calc_d_day("bad-date") is None


def test_extract_d_day_basic():
    assert extract_d_day("접수중 D-7") == 7


def test_extract_d_day_with_spaces():
    assert extract_d_day("D - 14 마감") == 14


def test_extract_d_day_d_day_keyword():
    assert extract_d_day("D-Day 입니다") == 0
    assert extract_d_day("아무것도 없음") is None


def test_extract_status_known_keywords():
    assert extract_status("D-3 접수중") == "open"
    assert extract_status("마감임박") == "closing"
    assert extract_status("접수예정") == "upcoming"


def test_extract_status_text_unknown_returns_none():
    assert extract_status_text("아무거나") is None
    assert extract_status("아무거나") is None


def test_extract_labeled_value_between_labels():
    text = "주최: 회사A 대상: 대학생 접수: 6.1 ~ 6.30"
    assert extract_labeled_value(text, "주최") == "회사A"
    assert extract_labeled_value(text, "대상") == "대학생"


def test_extract_labeled_value_missing():
    assert extract_labeled_value("대상: 학생", "주최") is None


def test_extract_title_from_text_with_label_marker():
    assert extract_title_from_text("멋진 콘테스트 주최: 회사") == "멋진 콘테스트"


def test_extract_title_from_text_without_marker():
    assert extract_title_from_text("그냥 제목") == "그냥 제목"


def test_clean_label_noise_strips_label_and_punctuation():
    assert clean_label_noise("주최: 회사A.", "주최") == "회사A"


def test_clean_label_noise_label_with_separator_only_returns_none():
    assert clean_label_noise("주최:", "주최") is None
    assert clean_label_noise("주최. ", "주최") is None


def test_extract_urls_from_text_finds_multiple():
    text = "참고 https://a.example.com 과 http://b.example.com/path."
    assert extract_urls_from_text(text) == [
        "https://a.example.com",
        "http://b.example.com/path",
    ]


def test_extract_urls_from_text_empty():
    assert extract_urls_from_text("URL 없음") == []


def test_find_same_domain_url_match():
    candidates = ["https://other.com/a", "https://example.com/b"]
    assert (
        find_same_domain_url("https://www.example.com/page", candidates)
        == "https://example.com/b"
    )


def test_find_same_domain_url_no_match():
    assert find_same_domain_url("https://x.com", ["https://y.com"]) is None


@pytest.mark.parametrize(
    "given, expected",
    [
        (None, True),
        ("https://www.contestkorea.com/sub/join.php", True),
        ("https://www.contestkorea.com/sub/join.php?str_no=1", True),
    ],
)
def test_should_replace_application_url_true_cases(given, expected):
    assert should_replace_application_url(given) is expected


def test_should_replace_application_url_false_for_real_link():
    assert should_replace_application_url("https://example.com/apply") is False


def test_unique_strings_preserves_order():
    assert unique_strings(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


def test_unique_strings_empty():
    assert unique_strings([]) == []


def test_unique_by_detail_url_dedups_and_drops_none():
    items = [
        {"detail_url": None, "title": "x"},
        {"detail_url": "https://a", "title": "first"},
        {"detail_url": "https://b", "title": "second"},
        {"detail_url": "https://a", "title": "dup"},
    ]
    result = unique_by_detail_url(items)
    assert [it["detail_url"] for it in result] == ["https://a", "https://b"]
    assert result[0]["title"] == "first"


def test_unique_by_detail_url_empty():
    assert unique_by_detail_url([]) == []
