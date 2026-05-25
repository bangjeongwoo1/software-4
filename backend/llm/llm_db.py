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


def fetch_contest_targets(*, limit: int | None = None, reprocess: bool = False) -> list[dict[str, Any]]:
    """Return contest_detail_2 rows with title context and optional processed filtering."""

    client = get_client()
    details = (
        client.table("contest_detail_2")
        .select(
            "contest_id,host_organization,main_field,target_text,reception_period_text,"
            "award_text,application_method,homepage_url,application_url,detail_text"
        )
        .order("contest_id")
        .execute()
        .data
        or []
    )

    contest_titles = {
        row["contest_id"]: row.get("title")
        for row in (
            client.table("contest").select("contest_id,title").execute().data or []
        )
    }

    processed_ids: set[int] = set()
    if not reprocess:
        try:
            processed_ids = {
                row["contest_id"]
                for row in (client.table("contest_llm").select("contest_id").execute().data or [])
            }
        except Exception as exc:
            if "contest_llm" not in str(exc):
                raise
            processed_ids = set()

    targets: list[dict[str, Any]] = []
    for detail in details:
        contest_id = detail.get("contest_id")
        if contest_id in processed_ids:
            continue
        if not has_any_contest_content(detail):
            continue
        detail["contest_title"] = contest_titles.get(contest_id)
        detail["raw_text"] = build_contest_text(detail)
        targets.append(detail)
        if limit and len(targets) >= limit:
            break

    return targets


def build_contest_text(detail: dict[str, Any]) -> str:
    parts = []
    if detail.get("contest_title"):
        parts.append(f"제목: {detail['contest_title']}")
    if detail.get("host_organization"):
        parts.append(f"주최/주관: {detail['host_organization']}")
    if detail.get("main_field"):
        parts.append(f"분야: {detail['main_field']}")
    if detail.get("target_text"):
        parts.append(f"참가대상: {detail['target_text']}")
    if detail.get("reception_period_text"):
        parts.append(f"접수기간: {detail['reception_period_text']}")
    if detail.get("award_text"):
        parts.append(f"시상내역: {detail['award_text']}")
    if detail.get("application_method"):
        parts.append(f"접수방법: {detail['application_method']}")
    if detail.get("homepage_url"):
        parts.append(f"홈페이지: {detail['homepage_url']}")
    if detail.get("application_url"):
        parts.append(f"접수 URL: {detail['application_url']}")
    if detail.get("detail_text"):
        parts.append(f"\n상세 본문:\n{detail['detail_text']}")
    return "\n".join(parts)


def has_any_contest_content(detail: dict[str, Any]) -> bool:
    return any(
        normalize_text(detail.get(key))
        for key in ("detail_text", "host_organization", "target_text", "award_text")
    )


def save_contest_llm(*, contest_id: int, contest_title: str | None, parsed: dict[str, Any]) -> None:
    """Upsert validated Gemini output into contest_llm."""

    payload = {
        "contest_id": contest_id,
        "contest_title": normalize_text(contest_title),
        "summary": normalize_text(parsed.get("summary")),
        "parsed_at": datetime.now(timezone.utc).isoformat(),
    }
    get_client().table("contest_llm").upsert(payload, on_conflict="contest_id").execute()


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None
