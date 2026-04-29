"""Executable scholarship crawler.

Usage:
    python -m crawler.crawler
    python crawler/crawler.py --list-url https://example.ac.kr/board/scholarship
"""

from __future__ import annotations

import argparse
import logging
import re
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from requests import RequestException

try:
    from . import config
    from .db import get_connection, upsert_scholarship
    from .parser import collect_detail_links, parse_detail_page
except ImportError:  # Allows running crawler.py directly.
    import config  # type: ignore
    from db import get_connection, upsert_scholarship  # type: ignore
    from parser import collect_detail_links, parse_detail_page  # type: ignore


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def fetch_html(session: requests.Session, url: str) -> str:
    """Fetch HTML and raise a clear error for network or HTTP failures."""
    try:
        response = session.get(url, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        encoding = _detect_encoding(response)
        return response.content.decode(encoding, errors="replace")
    except RequestException as exc:
        raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc


def _detect_encoding(response: requests.Response) -> str:
    """Prefer declared HTML charset over requests' guessed encoding."""
    content_type = response.headers.get("Content-Type", "")
    header_match = re.search(r"charset=([\w-]+)", content_type, flags=re.IGNORECASE)
    if header_match:
        return header_match.group(1)

    head = response.content[:2048].decode("ascii", errors="ignore")
    meta_match = re.search(r"<meta[^>]+charset=[\"']?([\w-]+)", head, flags=re.IGNORECASE)
    if meta_match:
        return meta_match.group(1)

    return response.encoding or response.apparent_encoding or "utf-8"


def crawl(list_url: str, limit: int | None = None, pages: int = 1) -> int:
    """Collect scholarship notices from list pages and save them to MySQL."""
    if not list_url:
        raise ValueError("LIST_URL is required. Set SCHOLARSHIP_LIST_URL or pass --list-url.")
    if pages < 1:
        raise ValueError("pages must be greater than or equal to 1.")

    saved_count = 0
    session = requests.Session()
    session.headers.update({"User-Agent": config.USER_AGENT})

    detail_urls: list[str] = []
    for page_index in range(1, pages + 1):
        page_url = _build_page_url(list_url, page_index)
        logger.info("Fetching list page %d/%d: %s", page_index, pages, page_url)
        list_html = fetch_html(session, page_url)
        page_detail_urls = collect_detail_links(list_html, page_url)

        if not page_detail_urls:
            logger.info("No detail links found on page %d. Stop collecting list pages.", page_index)
            break

        detail_urls.extend(page_detail_urls)
        detail_urls = list(_iter_unique(detail_urls))

        if limit is not None and len(detail_urls) >= limit:
            detail_urls = detail_urls[:limit]
            break

    logger.info("Collected %d detail links", len(detail_urls))

    connection = get_connection()
    try:
        for detail_url in detail_urls:
            try:
                logger.info("Fetching detail page: %s", detail_url)
                detail_html = fetch_html(session, detail_url)
                scholarship = parse_detail_page(detail_html, detail_url)

                if not scholarship["title"]:
                    logger.warning("Skipped page without title: %s", detail_url)
                    continue

                upsert_scholarship(connection, scholarship)
                saved_count += 1
                logger.info("Saved: %s", scholarship["title"])
            except Exception as exc:
                # Continue crawling other notices even when one page fails.
                logger.exception("Failed to process %s: %s", detail_url, exc)
    finally:
        connection.close()

    logger.info("Done. Saved or updated %d scholarships", saved_count)
    return saved_count


def _iter_unique(urls: Iterable[str]) -> Iterable[str]:
    seen: set[str] = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        yield url


def _build_page_url(list_url: str, page_index: int) -> str:
    """Return a list URL for the requested pageIndex query parameter."""
    parts = urlsplit(list_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["pageIndex"] = str(page_index)

    if parts.path.endswith("/janghak/list.do"):
        query.setdefault("searchYn", "Y")
        query.setdefault("searchCl2", "1")
        query.setdefault("searchCondition", "1")
        query.setdefault("pageItm", "10")
        query.setdefault("searchOrderSort", "0")
        query.setdefault("searchGbn", "0")

    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl scholarship notices into MySQL.")
    parser.add_argument("--list-url", default=config.LIST_URL, help="Scholarship notice list URL")
    parser.add_argument("--limit", type=int, default=None, help="Maximum detail pages to crawl")
    parser.add_argument("--pages", type=int, default=1, help="Number of list pages to crawl")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    crawl(args.list_url, args.limit, args.pages)
