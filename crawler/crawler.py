"""Executable renewal crawler for Kangwon scholarship sources."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections.abc import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from requests import RequestException

try:
    from . import config
    from . import db
    from .parser import (
        build_status,
        extract_period,
        normalize_detail_url,
        parse_customized_detail,
        parse_customized_list,
        parse_notice_detail,
        parse_notice_list,
    )
except ImportError:  # pragma: no cover
    import config  # type: ignore
    import db  # type: ignore
    from parser import (  # type: ignore
        build_status,
        extract_period,
        normalize_detail_url,
        parse_customized_detail,
        parse_customized_list,
        parse_notice_detail,
        parse_notice_list,
    )


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def crawl(source: str = "all", pages: int = 1, limit: int | None = None, dry_run: bool = False) -> int:
    """Crawl one or both Kangwon scholarship sources."""

    if pages < 1:
        raise ValueError("pages must be >= 1")
    if source not in {"customized", "notice", "all"}:
        raise ValueError("source must be one of: customized, notice, all")

    session = requests.Session()
    session.headers.update({"User-Agent": config.USER_AGENT})

    total = 0
    if source in {"customized", "all"}:
        total += crawl_customized(session, pages=pages, limit=limit, dry_run=dry_run)
    if source in {"notice", "all"}:
        total += crawl_notice(session, pages=pages, limit=limit, dry_run=dry_run)

    return total


def crawl_customized(
    session: requests.Session,
    *,
    pages: int,
    limit: int | None,
    dry_run: bool,
) -> int:
    """Crawl customized scholarship pages. List POST establishes the session cookie."""

    list_items: list[dict] = []

    for page_index in range(1, pages + 1):
        page_url, post_data = build_customized_list_request(page_index)
        logger.info("Fetching customized list page %s/%s", page_index, pages)
        html = fetch_html(session, page_url, data=post_data)
        page_items = parse_customized_list(html, page_url)
        if not page_items:
            logger.info("No customized items found on page %s", page_index)
            break
        list_items.extend(page_items)
        list_items = unique_by_detail_url(list_items)
        if limit and len(list_items) >= limit:
            list_items = list_items[:limit]
            break

    saved = 0
    for list_item in list_items:
        detail_url = list_item["detail_url"]
        logger.info("Processing customized detail: %s", detail_url)
        detail_html = fetch_html(session, detail_url)
        detail = parse_customized_detail(detail_html, detail_url, list_item)
        status = "open"

        if dry_run:
            emit_dry_run("customized", list_item, detail, status)
        else:
            db.save_customized(list_item, detail, status=status)
        saved += 1

    logger.info("Customized crawl complete. Processed %s items", saved)
    return saved


def crawl_notice(
    session: requests.Session,
    *,
    pages: int,
    limit: int | None,
    dry_run: bool,
) -> int:
    """Crawl scholarship notice board pages."""

    list_items: list[dict] = []

    for page_index in range(1, pages + 1):
        page_url = build_notice_list_url(page_index)
        logger.info("Fetching notice list page %s/%s", page_index, pages)
        html = fetch_html(session, page_url)
        page_items = parse_notice_list(html, page_url)
        if not page_items:
            logger.info("No notice items found on page %s", page_index)
            break
        list_items.extend(page_items)
        list_items = unique_by_detail_url(list_items)
        if limit and len(list_items) >= limit:
            list_items = list_items[:limit]
            break

    saved = 0
    for list_item in list_items:
        detail_url = list_item["detail_url"]
        logger.info("Processing notice detail: %s", detail_url)
        detail_html = fetch_html(session, detail_url)
        detail = parse_notice_detail(detail_html, detail_url, list_item)
        start_date, end_date = extract_period(detail.get("raw_text"))
        status = build_status(start_date, end_date)

        if dry_run:
            emit_dry_run("notice", list_item, detail, status)
        else:
            db.save_notice(list_item, detail, status=status)
        saved += 1

    logger.info("Notice crawl complete. Processed %s items", saved)
    return saved


def fetch_html(session: requests.Session, url: str, data: dict[str, str] | None = None) -> str:
    """Fetch HTML and decode using the server-declared charset when available."""

    try:
        if data is None:
            response = session.get(url, timeout=config.REQUEST_TIMEOUT)
        else:
            response = session.post(url, data=data, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
    except RequestException as exc:
        raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc

    encoding = detect_encoding(response)
    return response.content.decode(encoding, errors="replace")


def detect_encoding(response: requests.Response) -> str:
    content_type = response.headers.get("Content-Type", "")
    header_match = re.search(r"charset=([\w-]+)", content_type, flags=re.IGNORECASE)
    if header_match:
        return header_match.group(1)

    head = response.content[:2048].decode("ascii", errors="ignore")
    meta_match = re.search(r"<meta[^>]+charset=[\"']?([\w-]+)", head, flags=re.IGNORECASE)
    if meta_match:
        return meta_match.group(1)

    return response.encoding or response.apparent_encoding or "utf-8"


def build_customized_list_request(page_index: int) -> tuple[str, dict[str, str]]:
    parts = urlsplit(config.CUSTOMIZED_LIST_URL)
    page_url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    post_data = {
        "searchYn": "Y",
        "pageIndex": str(page_index),
        "searchCondition": "1",
        "searchKeyword": "",
        "searchKeyword2": "",
        "searchCl2": "1",
        "janghakGbnAll": "",
        "searchMultiChar": "",
        "searchMultiStdnt": "",
        "gradeAll": "",
        "searchMultiGrade": "",
        "tierRadio": "511",
        "searchMultiTier": "511",
        "searchCl9": "",
        "searchCl10": "",
        "pageItm": "10",
    }
    return page_url, post_data


def build_notice_list_url(page_index: int) -> str:
    parts = urlsplit(config.NOTICE_LIST_URL)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["pageIndex"] = str(page_index)
    query.setdefault("pageItm", "10")
    query.setdefault("searchOrderSort", "0")
    query.setdefault("searchGbn", "0")
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def unique_by_detail_url(items: Iterable[dict]) -> list[dict]:
    seen = set()
    results = []
    for item in items:
        detail_url = normalize_detail_url(item["detail_url"])
        if detail_url in seen:
            continue
        seen.add(detail_url)
        item = {**item, "detail_url": detail_url}
        results.append(item)
    return results


def emit_dry_run(source: str, list_item: dict, detail: dict, status: str) -> None:
    payload = {
        "source": source,
        "status": status,
        "list": list_item,
        "detail": compact_for_dry_run(detail),
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace") + b"\n")


def compact_for_dry_run(detail: dict) -> dict:
    """Keep dry-run readable while preserving DB payloads in normal runs."""

    compacted = dict(detail)
    raw_html = compacted.get("raw_html")
    if isinstance(raw_html, str) and len(raw_html) > 500:
        compacted["raw_html"] = f"[omitted in dry-run: {len(raw_html)} chars]"
    return compacted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Kangwon scholarship renewal crawler")
    parser.add_argument(
        "--source",
        choices=["customized", "notice", "all"],
        default="all",
        help="Which source to crawl",
    )
    parser.add_argument("--pages", type=int, default=1, help="List pages to crawl per source")
    parser.add_argument("--limit", type=int, default=None, help="Max detail pages per source")
    parser.add_argument("--dry-run", action="store_true", help="Parse and print without DB writes")
    return parser.parse_args()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    total = crawl(source=args.source, pages=args.pages, limit=args.limit, dry_run=args.dry_run)
    logger.info("Total processed: %s", total)
