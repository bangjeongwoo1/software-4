"""Tests for ``backend/contest/contest_crawler.py``.

requests.Session 과 db 모듈은 monkeypatch + MagicMock 으로 격리한다.
총 12개 케이스.
"""

from __future__ import annotations

import io
import json
import sys
from unittest.mock import MagicMock

import pytest
from requests import RequestException

from contest import contest_crawler as crawler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class FakeResponse:
    def __init__(self, content: bytes, status: int = 200):
        self.content = content
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RequestException(f"status {self.status_code}")


# ---------------------------------------------------------------------------
# build_list_url  (2 cases)
# ---------------------------------------------------------------------------
def test_build_list_url_includes_page_param():
    url = crawler.build_list_url(3)
    assert "page=3" in url
    assert url.startswith("https://www.contestkorea.com/sub/list.php?")


def test_build_list_url_different_pages():
    assert "page=1" in crawler.build_list_url(1)
    assert "page=99" in crawler.build_list_url(99)


# ---------------------------------------------------------------------------
# unique_by_detail_url  (2 cases)
# ---------------------------------------------------------------------------
def test_unique_by_detail_url_dedups_after_normalization():
    items = [
        {"detail_url": "/sub/view.php?int_gbn=1&str_no=1", "title": "first"},
        {"detail_url": "/sub/view.php?int_gbn=1&str_no=1&extra=x", "title": "dup"},
        {"detail_url": "/sub/view.php?int_gbn=1&str_no=2", "title": "second"},
    ]
    result = crawler.unique_by_detail_url(items)
    assert [it["title"] for it in result] == ["first", "second"]
    # detail_url 도 정규화된 형태로 바뀜
    assert all("extra" not in it["detail_url"] for it in result)


def test_unique_by_detail_url_empty():
    assert crawler.unique_by_detail_url([]) == []


# ---------------------------------------------------------------------------
# fetch_html  (3 cases)
# ---------------------------------------------------------------------------
def test_fetch_html_decodes_utf8():
    session = MagicMock()
    session.get.return_value = FakeResponse("안녕 hello".encode("utf-8"))
    assert crawler.fetch_html(session, "https://x.com") == "안녕 hello"


def test_fetch_html_raises_on_request_exception():
    session = MagicMock()
    session.get.side_effect = RequestException("network down")
    with pytest.raises(RuntimeError, match="Failed to fetch"):
        crawler.fetch_html(session, "https://x.com")


def test_fetch_html_raises_on_http_error():
    session = MagicMock()
    session.get.return_value = FakeResponse(b"err", status=500)
    with pytest.raises(RuntimeError, match="Failed to fetch"):
        crawler.fetch_html(session, "https://x.com")


# ---------------------------------------------------------------------------
# compact_for_dry_run  (2 cases)
# ---------------------------------------------------------------------------
def test_compact_for_dry_run_shortens_long_detail_text():
    long_text = "x" * 2000
    out = crawler.compact_for_dry_run({"detail_text": long_text, "other": "ok"})
    assert out["detail_text"].startswith("[omitted in dry-run")
    assert out["other"] == "ok"


def test_compact_for_dry_run_keeps_short_text():
    out = crawler.compact_for_dry_run({"detail_text": "짧음"})
    assert out["detail_text"] == "짧음"


# ---------------------------------------------------------------------------
# emit_dry_run  (1 case)
# ---------------------------------------------------------------------------
def test_emit_dry_run_prints_json(capsys):
    list_item = {"title": "t", "status": "open", "detail_url": "u"}
    detail = {"detail_text": "short"}
    crawler.emit_dry_run(list_item, detail)
    captured = capsys.readouterr().out
    payload = json.loads(captured)
    assert payload["status"] == "open"
    assert payload["list"]["title"] == "t"
    assert payload["detail"]["detail_text"] == "short"


# ---------------------------------------------------------------------------
# crawl validation  (2 cases)
# ---------------------------------------------------------------------------
def test_crawl_rejects_pages_lt_1():
    with pytest.raises(ValueError, match="pages"):
        crawler.crawl(pages=0)


def test_crawl_rejects_negative_sleep():
    with pytest.raises(ValueError, match="sleep"):
        crawler.crawl(sleep=-1)
