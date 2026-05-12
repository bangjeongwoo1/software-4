"""Supabase persistence and source selection for LLM notice parsing."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import llm_config as config


_client = None


def get_client():
    """Create the Supabase client lazily so dry-run still validates only Gemini when needed."""

    global _client
    if _client is None:
        config.validate_db_config()
        from supabase import create_client

        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _client


def fetch_notice_targets(*, limit: int | None = None, reprocess: bool = False) -> list[dict[str, Any]]:
    """Return notice_detail_2 rows with title context and optional processed filtering."""

    client = get_client()
    details = (
        client.table("notice_detail_2")
        .select("scholarship_id,title,raw_text,attachment_file_url,attachment_file_type,image_file_url")
        .order("scholarship_id")
        .execute()
        .data
        or []
    )

    list_titles = {
        row["scholarship_id"]: row.get("title")
        for row in (
            client.table("notice_detail_1")
            .select("scholarship_id,title")
            .execute()
            .data
            or []
        )
    }

    processed_ids: set[int] = set()
    if not reprocess:
        try:
            processed_ids = {
                row["scholarship_id"]
                for row in (client.table("notice_llm").select("scholarship_id").execute().data or [])
            }
        except Exception as exc:
            if "notice_llm" not in str(exc):
                raise
            processed_ids = set()

    targets: list[dict[str, Any]] = []
    for detail in details:
        scholarship_id = detail.get("scholarship_id")
        if scholarship_id in processed_ids:
            continue
        if not has_any_source_content(detail):
            continue
        detail["notice_title"] = list_titles.get(scholarship_id) or detail.get("title")
        targets.append(detail)
        if limit and len(targets) >= limit:
            break

    return targets


def has_any_source_content(detail: dict[str, Any]) -> bool:
    return any(
        normalize_text(detail.get(key))
        for key in ("raw_text", "attachment_file_url", "image_file_url")
    )


def save_notice_llm(*, scholarship_id: int, notice_title: str | None, parsed: dict[str, Any]) -> None:
    """Upsert validated Gemini output into notice_llm."""

    payload = {
        "scholarship_id": scholarship_id,
        "notice_title": normalize_text(notice_title),
        "summary": normalize_text(parsed.get("summary")),
        "amount_text": normalize_text(parsed.get("amount_text")),
        "department_text": normalize_text(parsed.get("department_text")),
        "grade_text": normalize_text(parsed.get("grade_text")),
        "grade_min": parsed.get("grade_min"),
        "grade_max": parsed.get("grade_max"),
        "gpa_min": parsed.get("gpa_min"),
        "application_start_date": parsed.get("application_start_date"),
        "application_close_date": parsed.get("application_close_date"),
        "parsed_at": datetime.now(timezone.utc).isoformat(),
    }
    get_client().table("notice_llm").upsert(payload, on_conflict="scholarship_id").execute()


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None
