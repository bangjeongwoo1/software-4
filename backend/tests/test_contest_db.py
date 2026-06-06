"""Tests for ``backend/contest/contest_db.py``.

Supabase 클라이언트는 MagicMock 으로 모킹하기 때문에 실제 네트워크/DB가 필요 없다.
총 10개 케이스.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from contest import contest_db


# ---------------------------------------------------------------------------
# normalize_payload  (3 cases)
# ---------------------------------------------------------------------------
def test_normalize_payload_empty_string_becomes_none():
    result = contest_db.normalize_payload({"title": "", "host": "회사"})
    assert result["title"] is None
    assert result["host"] == "회사"


def test_normalize_payload_strips_whitespace():
    result = contest_db.normalize_payload({"title": "  hello  "})
    assert result["title"] == "hello"


def test_normalize_payload_passes_through_non_strings():
    result = contest_db.normalize_payload({"d_day": 7, "items": [1, 2], "flag": True, "x": None})
    assert result == {"d_day": 7, "items": [1, 2], "flag": True, "x": None}


# ---------------------------------------------------------------------------
# upsert_common_contest validation  (1 case)
# ---------------------------------------------------------------------------
def test_upsert_common_contest_rejects_invalid_status():
    with pytest.raises(ValueError, match="Invalid contest status"):
        contest_db.upsert_common_contest(
            site_id=1, title="t", detail_url="https://x", status="bogus"
        )


# ---------------------------------------------------------------------------
# save_contest validation  (3 cases)
# ---------------------------------------------------------------------------
def test_save_contest_requires_title():
    with pytest.raises(ValueError, match="title and detail_url"):
        contest_db.save_contest(
            {"detail_url": "https://x", "status": "open"},
            {},
        )


def test_save_contest_requires_detail_url():
    with pytest.raises(ValueError, match="title and detail_url"):
        contest_db.save_contest(
            {"title": "t", "status": "open"},
            {},
        )


def test_save_contest_requires_valid_status():
    with pytest.raises(ValueError, match="valid status"):
        contest_db.save_contest(
            {"title": "t", "detail_url": "https://x", "status": "weird"},
            {},
        )


# ---------------------------------------------------------------------------
# get_or_create_source_site  (2 cases)
# ---------------------------------------------------------------------------
def _make_client_with_existing_site(site_id: int = 7) -> MagicMock:
    client = MagicMock()
    chain = client.table.return_value.select.return_value.eq.return_value.limit.return_value
    chain.execute.return_value.data = [{"site_id": site_id}]
    return client


def _make_client_inserting_site(new_site_id: int = 11) -> MagicMock:
    client = MagicMock()
    # SELECT 결과 비어있게
    select_chain = client.table.return_value.select.return_value.eq.return_value.limit.return_value
    select_chain.execute.return_value.data = []
    # INSERT 후 결과
    insert_chain = client.table.return_value.insert.return_value
    insert_chain.execute.return_value.data = [{"site_id": new_site_id}]
    return client


def test_get_or_create_source_site_returns_existing_id(monkeypatch):
    client = _make_client_with_existing_site(site_id=7)
    monkeypatch.setattr(contest_db, "get_client", lambda: client)
    assert contest_db.get_or_create_source_site() == 7


def test_get_or_create_source_site_inserts_when_missing(monkeypatch):
    client = _make_client_inserting_site(new_site_id=11)
    monkeypatch.setattr(contest_db, "get_client", lambda: client)
    assert contest_db.get_or_create_source_site() == 11
    # insert 가 한 번이라도 호출됐는지
    client.table.return_value.insert.assert_called_once()


# ---------------------------------------------------------------------------
# save_contest happy path  (1 case)
# ---------------------------------------------------------------------------
def test_save_contest_happy_path(monkeypatch):
    client = MagicMock()

    # source_site SELECT → 기존 id 반환
    select_chain = client.table.return_value.select.return_value.eq.return_value.limit.return_value
    select_chain.execute.return_value.data = [{"site_id": 5}]

    # 모든 upsert().execute() 가 contest_id 를 반환하도록
    upsert_chain = client.table.return_value.upsert.return_value
    upsert_chain.execute.return_value.data = [{"contest_id": 99}]

    monkeypatch.setattr(contest_db, "get_client", lambda: client)

    contest_id = contest_db.save_contest(
        {
            "title": "테스트 콘테스트",
            "detail_url": "https://www.contestkorea.com/sub/view.php?int_gbn=1&str_no=1",
            "status": "open",
            "host": "회사",
            "target_text": "대학생",
            "reception_start": "2026-06-01",
            "reception_end": "2026-06-30",
            "d_day": 7,
        },
        {
            "host_organization": "회사",
            "detail_text": "본문",
        },
    )

    assert contest_id == 99
    # 최소한 source_site / contest / contest_detail_1 / contest_detail_2 4개의 table 호출이 있어야 함
    table_names = [call.args[0] for call in client.table.call_args_list]
    assert "source_site" in table_names
    assert "contest" in table_names
    assert "contest_detail_1" in table_names
    assert "contest_detail_2" in table_names
