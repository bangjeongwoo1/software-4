"""Configuration for the ContestKorea crawler."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


CONTEST_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CONTEST_DIR.parent
load_dotenv(PROJECT_DIR / ".env")


BASE_URL = os.getenv("CONTEST_BASE_URL", "https://www.contestkorea.com")
LIST_URL = os.getenv("CONTEST_LIST_URL", f"{BASE_URL}/sub/list.php")

SITE_NAME = os.getenv("CONTEST_SITE_NAME", "콘테스트코리아")
SOURCE_TYPE = "contestkorea"

LIST_PARAMS = {
    "displayrow": "12",
    "int_gbn": "1",
    "Txt_sGn": "1",
    "Txt_key": "all",
    "Txt_word": "",
    "Txt_bcode": "030310001",
    "Txt_code1[0]": "30",
    "Txt_code1[1]": "76",
    "Txt_code1[2]": "58",
    "Txt_aarea": "",
    "Txt_area[0]": "31",
    "Txt_area[1]": "32",
    "Txt_area[2]": "33",
    "Txt_sortkey": "a.int_sort",
    "Txt_sortword": "desc",
    "Txt_ahost": "1",
    "Txt_host": "",
    "Txt_award": "",
    "Txt_award2": "",
    "Txt_code3": "",
    "Txt_tipyn": "",
    "Txt_comment": "",
    "Txt_resultyn": "",
    "Txt_actcode": "",
}

STATUS_MAP = {
    "접수예정": "upcoming",
    "접수중": "open",
    "마감임박": "closing",
}
VALID_STATUSES = set(STATUS_MAP.values())

REQUEST_TIMEOUT = int(os.getenv("CRAWLER_REQUEST_TIMEOUT", "15"))
USER_AGENT = os.getenv(
    "CRAWLER_USER_AGENT",
    "Mozilla/5.0 (compatible; ContestKoreaCrawler/1.0)",
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


def validate_db_config() -> None:
    """Validate DB config only when a real DB write is requested."""

    missing = []
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")

    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
