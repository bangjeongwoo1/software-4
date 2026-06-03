"""Configuration for Gemini-based notice parsing."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


LLM_DIR = Path(__file__).resolve().parent
PROJECT_DIR = LLM_DIR.parent.parent
PROMPT_DIR = LLM_DIR / "prompts"
load_dotenv(PROJECT_DIR / ".env")


SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")

REQUEST_TIMEOUT = int(os.getenv("LLM_REQUEST_TIMEOUT", os.getenv("CRAWLER_REQUEST_TIMEOUT", "20")))
DEFAULT_SLEEP_SECONDS = float(os.getenv("LLM_DEFAULT_SLEEP", "4"))
USER_AGENT = os.getenv(
    "CRAWLER_USER_AGENT",
    "Mozilla/5.0 (compatible; KangwonNoticeLLMParser/1.0)",
)

SYSTEM_PROMPTS = {
    "notice": (PROMPT_DIR / "notice_extraction.txt").read_text(encoding="utf-8").strip(),
    "contest": (PROMPT_DIR / "contest_extraction.txt").read_text(encoding="utf-8").strip(),
}


def validate_db_config() -> None:
    missing = []
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def validate_gemini_config() -> None:
    if not GEMINI_API_KEY:
        raise RuntimeError("Missing required environment variable: GEMINI_API_KEY")
