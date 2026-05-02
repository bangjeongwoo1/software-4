"""Renewal crawler configuration.

This module intentionally does not depend on the old crawler config.  It keeps
the defaults aligned with kangwon_scholarship_crawling_design.md while allowing
the current .env values to override them.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


CRAWLER_DIR = Path(__file__).resolve().parent
load_dotenv(CRAWLER_DIR / ".env")


BASE_URL = os.getenv("SCHOLARSHIP_BASE_URL", "https://www.kangwon.ac.kr")

CUSTOMIZED_LIST_URL = os.getenv(
    "SCHOLARSHIP_JANGHAK_URL",
    "https://www.kangwon.ac.kr/ko/extn/90/janghak/list.do",
)

NOTICE_LIST_URL = os.getenv(
    "SCHOLARSHIP_LIST_URL",
    "https://www.kangwon.ac.kr/ko/bbs/750/list.do",
)

REQUEST_TIMEOUT = int(os.getenv("CRAWLER_REQUEST_TIMEOUT", "15"))

USER_AGENT = os.getenv(
    "CRAWLER_USER_AGENT",
    "Mozilla/5.0 (compatible; ScholarshipCrawler/Renewal)",
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


SOURCE_CUSTOMIZED = "customized"
SOURCE_NOTICE = "notice"

CUSTOMIZED_SITE_NAME = "강원대 맞춤 장학조회"
NOTICE_SITE_NAME = "강원대 장학공지"


def validate_db_config() -> None:
    """Validate DB config only when a real DB write is requested."""

    missing = []
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")

    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

