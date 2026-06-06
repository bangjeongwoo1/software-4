"""Tests for ``backend/scholarship/crawler.py``.

requests.Session 은 MagicMock 으로 격리한다.
총 13개 케이스.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from requests import RequestException

from scholarship import crawler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class FakeResponse:
    def __init__(self, content: bytes, *, status: int = 200, headers: dict | None = None,
                 encoding: str | None = None, apparent_encoding: str | None = None):
        self.content = content
        self.status_code = status
        self.headers = headers or {}
        self.encoding = encoding
        self.apparent_encoding = apparent_encoding

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RequestException(f"status {self.status_code}")


# ---------------------------------------------------------------------------
# build_customized_list_request  (2 cases)
# ---------------------------------------------------------------------------
def test_build_customized_list_request_page_index_in_post_data():
    url, post = crawler.build_customized_list_request(3)
    assert post["pageIndex"] == "3"
    assert post["searchYn"] == "Y"
    assert post["pageItm"] == "10"
    # URL 에서 query string 은 제거됨
    assert "?" not in url


def test_build_customized_list_request_different_pages():
    _, post1 = crawler.build_customized_list_request(1)
    _, post99 = crawler.build_customized_list_request(99)
    assert post1["pageIndex"] == "1"
    assert post99["pageIndex"] == "99"


# ---------------------------------------------------------------------------
# build_notice_list_url  (2 cases)
# ---------------------------------------------------------------------------
def test_build_notice_list_url_adds_page_index():
    url = crawler.build_notice_list_url(2)
    assert "pageIndex=2" in url


def test_build_notice_list_url_defaults():
    url = crawler.build_notice_list_url(1)
    assert "pageItm=10" in url
    assert "searchOrderSort=0" in url
    assert "searchGbn=0" in url


# ---------------------------------------------------------------------------
# unique_by_detail_url  (2 cases)
# ---------------------------------------------------------------------------
def test_unique_by_detail_url_dedups_after_normalization():
    items = [
        {"detail_url": "https://www.kangwon.ac.kr/x?janghakSn=1", "title": "first"},
        {"detail_url": "https://www.kangwon.ac.kr/x?janghakSn=1&extra=y", "title": "dup"},
        {"detail_url": "https://www.kangwon.ac.kr/x?janghakSn=2", "title": "second"},
    ]
    result = crawler.unique_by_detail_url(items)
    assert [it["title"] for it in result] == ["first", "second"]


def test_unique_by_detail_url_empty_input():
    assert crawler.unique_by_detail_url([]) == []


# ---------------------------------------------------------------------------
# detect_encoding  (3 cases)
# ---------------------------------------------------------------------------
def test_detect_encoding_from_header():
    response = FakeResponse(
        b"<html></html>",
        headers={"Content-Type": "text/html; charset=EUC-KR"},
    )
    assert crawler.detect_encoding(response) == "EUC-KR"


def test_detect_encoding_from_meta():
    response = FakeResponse(
        b"<html><head><meta charset='UTF-8'></head></html>",
        headers={"Content-Type": "text/html"},
    )
    assert crawler.detect_encoding(response) == "UTF-8"


def test_detect_encoding_falls_back_to_response_encoding():
    response = FakeResponse(
        b"<html></html>",
        headers={"Content-Type": "text/html"},
        encoding="ISO-8859-1",
    )
    assert crawler.detect_encoding(response) == "ISO-8859-1"


# ---------------------------------------------------------------------------
# fetch_html  (2 cases)
# ---------------------------------------------------------------------------
def test_fetch_html_get_request_decodes_utf8():
    session = MagicMock()
    session.get.return_value = FakeResponse(
        "안녕 hello".encode("utf-8"),
        headers={"Content-Type": "text/html; charset=utf-8"},
    )
    assert crawler.fetch_html(session, "https://x.com") == "안녕 hello"
    # GET 인지 확인
    session.get.assert_called_once()
    session.post.assert_not_called()


def test_fetch_html_raises_runtime_error_on_failure():
    session = MagicMock()
    session.get.side_effect = RequestException("network down")
    with pytest.raises(RuntimeError, match="Failed to fetch"):
        crawler.fetch_html(session, "https://x.com")


# ---------------------------------------------------------------------------
# emit_dry_run / compact_for_dry_run  (3 cases)
# ---------------------------------------------------------------------------
def test_compact_for_dry_run_shortens_long_raw_html():
    long_html = "x" * 1000
    out = crawler.compact_for_dry_run({"raw_html": long_html, "other": "ok"})
    assert out["raw_html"].startswith("[omitted in dry-run")
    assert out["other"] == "ok"


def test_compact_for_dry_run_keeps_short_raw_html():
    out = crawler.compact_for_dry_run({"raw_html": "짧음"})
    assert out["raw_html"] == "짧음"


def test_emit_dry_run_prints_json_payload(capsys):
    crawler.emit_dry_run(
        "customized",
        {"title": "장학A", "detail_url": "https://x"},
        {"summary": "요약"},
        status="open",
    )
    captured = capsys.readouterr().out
    payload = json.loads(captured)
    assert payload["source"] == "customized"
    assert payload["status"] == "open"
    assert payload["list"]["title"] == "장학A"
    assert payload["detail"]["summary"] == "요약"


# ---------------------------------------------------------------------------
# crawl validation  (2 cases)
# ---------------------------------------------------------------------------
def test_crawl_rejects_pages_lt_1():
    with pytest.raises(ValueError, match="pages"):
        crawler.crawl(pages=0)


def test_crawl_rejects_unknown_source():
    with pytest.raises(ValueError, match="source"):
        crawler.crawl(source="bogus")
