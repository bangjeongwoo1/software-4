"""Supabase persistence layer for the renewal crawler schema."""

from __future__ import annotations

from typing import Any

try:
    from . import config
except ImportError:  # pragma: no cover
    import config  # type: ignore


_client = None


def get_client():
    """Create the Supabase client lazily so dry-run does not need DB setup."""

    global _client
    if _client is None:
        config.validate_db_config()
        from supabase import create_client

        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _client


def get_or_create_source_site(site_name: str, base_url: str, site_type: str = "scholarship") -> int:
    client = get_client()
    existing = (
        client.table("source_site")
        .select("site_id")
        .eq("site_name", site_name)
        .limit(1)
        .execute()
    )
    if existing.data:
        return existing.data[0]["site_id"]

    created = (
        client.table("source_site")
        .insert({"site_name": site_name, "base_url": base_url, "site_type": site_type})
        .execute()
    )
    return created.data[0]["site_id"]


def upsert_common_scholarship(
    *,
    site_name: str,
    source_type: str,
    title: str,
    detail_url: str,
    status: str = "open",
) -> int:
    """Upsert the common scholarship parent row and return scholarship_id."""

    client = get_client()
    site_id = get_or_create_source_site(site_name, config.BASE_URL)
    normalized_status = status if status in {"open", "closed", "upcoming"} else "open"

    result = (
        client.table("scholarship")
        .upsert(
            {
                "site_id": site_id,
                "source_type": source_type,
                "title": title,
                "detail_url": detail_url,
                "status": normalized_status,
            },
            on_conflict="detail_url",
        )
        .execute()
    )
    return result.data[0]["scholarship_id"]


def save_customized(list_item: dict[str, Any], detail: dict[str, Any], status: str = "open") -> int:
    """Save customized scholarship list/detail rows."""

    client = get_client()
    title = detail.get("title") or list_item.get("title")
    detail_url = list_item.get("detail_url") or detail.get("detail_url")
    if not title or not detail_url:
        raise ValueError("customized item requires title and detail_url")

    scholarship_id = upsert_common_scholarship(
        site_name=config.CUSTOMIZED_SITE_NAME,
        source_type=config.SOURCE_CUSTOMIZED,
        title=title,
        detail_url=detail_url,
        status=status,
    )

    client.table("customized_detail_1").upsert(
        {
            "scholarship_id": scholarship_id,
            "detail_url": detail_url,
            "title": list_item.get("title"),
            "scholarship_type": list_item.get("scholarship_type"),
            "benefit_type": list_item.get("benefit_type"),
            "summary": list_item.get("summary"),
        },
        on_conflict="scholarship_id",
    ).execute()

    detail_payload = {"scholarship_id": scholarship_id, **detail}
    detail_payload.pop("detail_url", None)
    client.table("customized_detail_2").upsert(
        detail_payload,
        on_conflict="scholarship_id",
    ).execute()

    return scholarship_id


def save_notice(list_item: dict[str, Any], detail: dict[str, Any], status: str = "open") -> int:
    """Save notice list/detail rows."""

    client = get_client()
    title = detail.get("title") or list_item.get("title")
    detail_url = detail.get("detail_url") or list_item.get("detail_url")
    if not title or not detail_url:
        raise ValueError("notice item requires title and detail_url")

    scholarship_id = upsert_common_scholarship(
        site_name=config.NOTICE_SITE_NAME,
        source_type=config.SOURCE_NOTICE,
        title=title,
        detail_url=detail_url,
        status=status,
    )

    client.table("notice_detail_1").upsert(
        {
            "scholarship_id": scholarship_id,
            "detail_url": detail_url,
            "is_notice": list_item.get("is_notice"),
            "campus_text": list_item.get("campus_text"),
            "title": list_item.get("title"),
            "author": list_item.get("author"),
            "registered_at": list_item.get("registered_at"),
            "view_count": list_item.get("view_count"),
        },
        on_conflict="scholarship_id",
    ).execute()

    detail_payload = {"scholarship_id": scholarship_id, **detail}
    detail_payload.pop("detail_url", None)
    client.table("notice_detail_2").upsert(
        detail_payload,
        on_conflict="scholarship_id",
    ).execute()

    return scholarship_id
