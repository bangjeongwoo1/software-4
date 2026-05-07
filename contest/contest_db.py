"""Supabase persistence for ContestKorea crawler data."""

from __future__ import annotations

from typing import Any

try:
    from . import contest_config as config
except ImportError:  # pragma: no cover
    import contest_config as config  # type: ignore


_client = None


def get_client():
    """Create the Supabase client lazily so dry-run does not need DB setup."""

    global _client
    if _client is None:
        config.validate_db_config()
        from supabase import create_client

        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _client


def get_or_create_source_site() -> int:
    """Return the ContestKorea source_site id, creating it when needed."""

    client = get_client()
    existing = (
        client.table("source_site")
        .select("site_id")
        .eq("site_name", config.SITE_NAME)
        .limit(1)
        .execute()
    )
    if existing.data:
        return existing.data[0]["site_id"]

    created = (
        client.table("source_site")
        .insert(
            {
                "site_name": config.SITE_NAME,
                "base_url": config.BASE_URL,
                "site_type": "contest",
            }
        )
        .execute()
    )
    return created.data[0]["site_id"]


def upsert_common_contest(*, site_id: int, title: str, detail_url: str, status: str) -> int:
    """Upsert the contest parent row and return contest_id."""

    if status not in config.VALID_STATUSES:
        raise ValueError(f"Invalid contest status: {status}")

    result = (
        get_client()
        .table("contest")
        .upsert(
            {
                "site_id": site_id,
                "source_type": config.SOURCE_TYPE,
                "title": title,
                "detail_url": detail_url,
                "status": status,
            },
            on_conflict="detail_url",
        )
        .execute()
    )
    return result.data[0]["contest_id"]


def save_contest(list_item: dict[str, Any], detail: dict[str, Any]) -> int:
    """Save list-level and detail-level contest data."""

    list_item = normalize_payload(list_item)
    detail = normalize_payload(detail)
    title = list_item.get("title") or detail.get("title")
    detail_url = list_item.get("detail_url") or detail.get("detail_url")
    status = list_item.get("status")

    if not title or not detail_url:
        raise ValueError("contest item requires title and detail_url")
    if status not in config.VALID_STATUSES:
        raise ValueError(f"contest item requires a valid status: {status}")

    site_id = get_or_create_source_site()
    contest_id = upsert_common_contest(
        site_id=site_id,
        title=title,
        detail_url=detail_url,
        status=status,
    )

    client = get_client()
    client.table("contest_detail_1").upsert(
        {
            "contest_id": contest_id,
            "detail_url": detail_url,
            "title": list_item.get("title"),
            "host": list_item.get("host"),
            "target_text": list_item.get("target_text"),
            "reception_start": list_item.get("reception_start"),
            "reception_end": list_item.get("reception_end"),
            "review_start": list_item.get("review_start"),
            "review_end": list_item.get("review_end"),
            "announcement_date": list_item.get("announcement_date"),
            "d_day": list_item.get("d_day"),
        },
        on_conflict="contest_id",
    ).execute()

    detail_payload = normalize_payload({"contest_id": contest_id, **detail})
    detail_payload.pop("detail_url", None)
    detail_payload.pop("title", None)
    client.table("contest_detail_2").upsert(
        detail_payload,
        on_conflict="contest_id",
    ).execute()

    return contest_id


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Convert empty strings to NULL while preserving real parsed values."""

    normalized = {}
    for key, value in payload.items():
        if isinstance(value, str):
            value = value.strip()
            normalized[key] = value or None
        else:
            normalized[key] = value
    return normalized
