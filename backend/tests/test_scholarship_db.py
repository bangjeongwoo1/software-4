"""Tests for ``backend/scholarship/db.py``.

Supabase 클라이언트는 MagicMock 으로 격리한다.
총 10개 케이스.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scholarship import db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _client_with_existing_site(site_id: int = 5) -> MagicMock:
    client = MagicMock()
    chain = client.table.return_value.select.return_value.eq.return_value.limit.return_value
    chain.execute.return_value.data = [{"site_id": site_id}]
    # 모든 upsert 가 scholarship_id 반환하도록
    upsert_chain = client.table.return_value.upsert.return_value
    upsert_chain.execute.return_value.data = [{"scholarship_id": 77}]
    return client


def _client_with_no_site(new_site_id: int = 11) -> MagicMock:
    client = MagicMock()
    select_chain = client.table.return_value.select.return_value.eq.return_value.limit.return_value
    select_chain.execute.return_value.data = []
    insert_chain = client.table.return_value.insert.return_value
    insert_chain.execute.return_value.data = [{"site_id": new_site_id}]
    upsert_chain = client.table.return_value.upsert.return_value
    upsert_chain.execute.return_value.data = [{"scholarship_id": 77}]
    return client


# ---------------------------------------------------------------------------
# get_or_create_source_site  (2 cases)
# ---------------------------------------------------------------------------
def test_get_or_create_source_site_returns_existing(monkeypatch):
    client = _client_with_existing_site(site_id=5)
    monkeypatch.setattr(db, "get_client", lambda: client)
    assert db.get_or_create_source_site("강원대 장학공지", "https://x") == 5


def test_get_or_create_source_site_inserts_when_missing(monkeypatch):
    client = _client_with_no_site(new_site_id=11)
    monkeypatch.setattr(db, "get_client", lambda: client)
    assert db.get_or_create_source_site("새 사이트", "https://x") == 11
    client.table.return_value.insert.assert_called_once()


# ---------------------------------------------------------------------------
# upsert_common_scholarship  (2 cases)
# ---------------------------------------------------------------------------
def test_upsert_common_scholarship_normalizes_status(monkeypatch):
    client = _client_with_existing_site(site_id=5)
    monkeypatch.setattr(db, "get_client", lambda: client)
    monkeypatch.setattr(db, "get_or_create_source_site", lambda *a, **k: 5)

    # 잘못된 status 는 "open" 으로 정규화됨 (예외 안 던짐)
    sid = db.upsert_common_scholarship(
        site_name="x",
        source_type="customized",
        title="t",
        detail_url="https://x",
        status="weird",
    )
    assert sid == 77
    args = client.table.return_value.upsert.call_args
    assert args[0][0]["status"] == "open"


def test_upsert_common_scholarship_keeps_valid_status(monkeypatch):
    client = _client_with_existing_site(site_id=5)
    monkeypatch.setattr(db, "get_client", lambda: client)
    monkeypatch.setattr(db, "get_or_create_source_site", lambda *a, **k: 5)

    db.upsert_common_scholarship(
        site_name="x",
        source_type="customized",
        title="t",
        detail_url="https://x",
        status="closed",
    )
    args = client.table.return_value.upsert.call_args
    assert args[0][0]["status"] == "closed"


# ---------------------------------------------------------------------------
# save_customized  (3 cases)
# ---------------------------------------------------------------------------
def test_save_customized_requires_title(monkeypatch):
    monkeypatch.setattr(db, "get_client", lambda: _client_with_existing_site())
    with pytest.raises(ValueError, match="title and detail_url"):
        db.save_customized({}, {"detail_url": "https://x"})


def test_save_customized_requires_detail_url(monkeypatch):
    monkeypatch.setattr(db, "get_client", lambda: _client_with_existing_site())
    with pytest.raises(ValueError, match="title and detail_url"):
        db.save_customized({"title": "t"}, {})


def test_save_customized_happy_path(monkeypatch):
    client = _client_with_existing_site()
    monkeypatch.setattr(db, "get_client", lambda: client)

    sid = db.save_customized(
        {
            "title": "장학A",
            "detail_url": "https://www.kangwon.ac.kr/x?janghakSn=1",
            "scholarship_type": "국가",
            "benefit_type": "등록금",
            "summary": "요약",
        },
        {"title": "장학A", "campus_text": "춘천"},
        status="open",
    )
    assert sid == 77
    table_names = [call.args[0] for call in client.table.call_args_list]
    assert "scholarship" in table_names
    assert "customized_detail_1" in table_names
    assert "customized_detail_2" in table_names


# ---------------------------------------------------------------------------
# save_notice  (3 cases)
# ---------------------------------------------------------------------------
def test_save_notice_requires_title(monkeypatch):
    monkeypatch.setattr(db, "get_client", lambda: _client_with_existing_site())
    with pytest.raises(ValueError, match="title and detail_url"):
        db.save_notice({}, {"detail_url": "https://x"})


def test_save_notice_requires_detail_url(monkeypatch):
    monkeypatch.setattr(db, "get_client", lambda: _client_with_existing_site())
    with pytest.raises(ValueError, match="title and detail_url"):
        db.save_notice({"title": "t"}, {})


def test_save_notice_happy_path(monkeypatch):
    client = _client_with_existing_site()
    monkeypatch.setattr(db, "get_client", lambda: client)

    sid = db.save_notice(
        {
            "title": "공지A",
            "detail_url": "https://www.kangwon.ac.kr/x?pstSn=42",
            "campus_text": "춘천",
            "author": "장학팀",
            "registered_at": "2026-06-05",
            "view_count": 123,
            "is_notice": True,
        },
        {"title": "공지A", "raw_text": "본문"},
        status="open",
    )
    assert sid == 77
    table_names = [call.args[0] for call in client.table.call_args_list]
    assert "scholarship" in table_names
    assert "notice_detail_1" in table_names
    assert "notice_detail_2" in table_names
