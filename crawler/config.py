"""Crawler and database configuration.

Values can be overridden with environment variables so the crawler can be
reused for different school notice boards without changing source code.
"""

import os


# Target pages -------------------------------------------------------------
# Example:
#   SCHOLARSHIP_LIST_URL=https://example.ac.kr/board/scholarship
BASE_URL = os.getenv("SCHOLARSHIP_BASE_URL", "")
LIST_URL = os.getenv("SCHOLARSHIP_LIST_URL", "")


# HTTP options -------------------------------------------------------------
REQUEST_TIMEOUT = int(os.getenv("CRAWLER_REQUEST_TIMEOUT", "10"))
USER_AGENT = os.getenv(
    "CRAWLER_USER_AGENT",
    "Mozilla/5.0 (compatible; ScholarshipCrawler/1.0)",
)


# CSS selectors ------------------------------------------------------------
# These defaults match many board-style pages. Override them in .env when the
# target site uses different markup.
LIST_LINK_SELECTOR = os.getenv("LIST_LINK_SELECTOR", "a")
TITLE_SELECTOR = os.getenv("TITLE_SELECTOR", "h1, h2, .title, .view-title")
CONTENT_SELECTOR = os.getenv("CONTENT_SELECTOR", "article, .content, .view-content, body")


# Database ----------------------------------------------------------------
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "scholarship_db")
DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")

