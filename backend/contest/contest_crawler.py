"""Executable ContestKorea crawler."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from collections.abc import Iterable
from urllib.parse import urlencode

import requests
from requests import RequestException

try:
    from . import contest_config as config
    from . import contest_db as db
    from .contest_parser import normalize_detail_url, parse_contest_detail, parse_contest_list
except ImportError:  # pragma: no cover
    import contest_config as config  # type: ignore
    import contest_db as db  # type: ignore
    from contest_parser import normalize_detail_url, parse_contest_detail, parse_contest_list  # type: ignore


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def crawl(*, pages: int = 1, limit: int | None = None, dry_run: bool = False, sleep: float = 0.7) -> int:
    """Crawl ContestKorea list/detail pages."""

    if pages < 1:
        raise ValueError("pages must be >= 1")
    if limit is not None and limit < 1:
        raise ValueError("limit must be >= 1")
    if sleep < 0:
        raise ValueError("sleep must be >= 0")

    session = requests.Session()
    session.headers.update({"User-Agent": config.USER_AGENT})

    list_items: list[dict] = []
    for page_index in range(1, pages + 1):
        page_url = build_list_url(page_index)
        logger.info("Fetching contest list page %s/%s", page_index, pages)
        html = fetch_html(session, page_url)
        page_items = parse_contest_list(html, page_url)
        if not page_items:
            logger.info("No valid contest items found on page %s", page_index)
            break

        list_items.extend(page_items)
        list_items = unique_by_detail_url(list_items)
        if limit and len(list_items) >= limit:
            list_items = list_items[:limit]
            break

        if sleep:
            time.sleep(sleep)

    saved = 0
    for list_item in list_items:
        detail_url = list_item["detail_url"]
        logger.info("Processing contest detail: %s", detail_url)
        detail_html = fetch_html(session, detail_url)
        detail = parse_contest_detail(detail_html, detail_url, list_item)

        if dry_run:
            emit_dry_run(list_item, detail)
        else:
            db.save_contest(list_item, detail)
        saved += 1

        if sleep:
            time.sleep(sleep)

    logger.info("Contest crawl complete. Processed %s items", saved)
    return saved


def fetch_html(session: requests.Session, url: str) -> str:
    """Fetch HTML and decode as UTF-8 per the design note."""

    try:
        response = session.get(url, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
    except RequestException as exc:
        raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc

    return response.content.decode("utf-8", errors="replace")


def build_list_url(page_index: int) -> str:
    params = dict(config.LIST_PARAMS)
    params["page"] = str(page_index)
    return f"{config.LIST_URL}?{urlencode(params)}"


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


def emit_dry_run(list_item: dict, detail: dict) -> None:
    payload = {
        "source": config.SOURCE_TYPE,
        "status": list_item.get("status"),
        "list": list_item,
        "detail": compact_for_dry_run(detail),
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace") + b"\n")


def compact_for_dry_run(detail: dict) -> dict:
    compacted = dict(detail)
    detail_text = compacted.get("detail_text")
    if isinstance(detail_text, str) and len(detail_text) > 1200:
        compacted["detail_text"] = f"[omitted in dry-run: {len(detail_text)} chars]"
    return compacted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ContestKorea crawler")
    parser.add_argument("--pages", type=int, default=1, help="List pages to crawl")
    parser.add_argument("--limit", type=int, default=None, help="Max detail pages to process")
    parser.add_argument("--dry-run", action="store_true", help="Parse and print without DB writes")
    parser.add_argument("--sleep", type=float, default=0.7, help="Delay between requests in seconds")
    return parser.parse_args()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    total = crawl(pages=args.pages, limit=args.limit, dry_run=args.dry_run, sleep=args.sleep)
    logger.info("Total processed: %s", total)
