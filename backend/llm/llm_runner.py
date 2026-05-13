"""CLI runner for Gemini-based scholarship notice parsing."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from typing import Any

from . import llm_config as config
from .llm_client import call_gemini
from .llm_db import fetch_notice_targets, save_notice_llm


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run(
    *,
    limit: int | None = None,
    dry_run: bool = False,
    reprocess: bool = False,
    sleep: float = config.DEFAULT_SLEEP_SECONDS,
    retries: int = 2,
    retry_wait: float = 20,
) -> int:
    """Process notice_detail_2 rows through Gemini."""

    if limit is not None and limit < 1:
        raise ValueError("limit must be >= 1")
    if sleep < 0:
        raise ValueError("sleep must be >= 0")
    if retries < 0:
        raise ValueError("retries must be >= 0")
    if retry_wait < 0:
        raise ValueError("retry_wait must be >= 0")

    targets = fetch_notice_targets(limit=limit, reprocess=reprocess)
    logger.info("Loaded %s notice target(s)", len(targets))

    processed = 0
    for index, target in enumerate(targets):
        scholarship_id = target["scholarship_id"]
        logger.info("Processing scholarship_id=%s", scholarship_id)
        try:
            parsed = call_gemini_with_retries(target, retries=retries, retry_wait=retry_wait)
        except Exception as exc:
            logger.exception("Skipping scholarship_id=%s after LLM failure: %s", scholarship_id, exc)
            continue

        if dry_run:
            emit_dry_run(target, parsed)
        else:
            save_notice_llm(
                scholarship_id=scholarship_id,
                notice_title=target.get("notice_title"),
                parsed=parsed,
            )
        processed += 1

        if sleep and index < len(targets) - 1:
            time.sleep(sleep)

    failed = len(targets) - processed
    logger.info("LLM notice parsing complete. Processed %s item(s), failed %s item(s)", processed, failed)
    return processed


def call_gemini_with_retries(target: dict[str, Any], *, retries: int, retry_wait: float) -> dict[str, Any]:
    """Call Gemini with simple retries for transient API errors."""

    scholarship_id = target.get("scholarship_id")
    for attempt in range(retries + 1):
        try:
            return call_gemini(
                raw_text=target.get("raw_text"),
                image_url=target.get("image_file_url"),
                pdf_url=target.get("attachment_file_url"),
            )
        except Exception:
            if attempt >= retries:
                raise
            wait_seconds = retry_wait * (attempt + 1)
            logger.warning(
                "Gemini call failed for scholarship_id=%s. Retrying %s/%s after %.1fs",
                scholarship_id,
                attempt + 1,
                retries,
                wait_seconds,
                exc_info=True,
            )
            if wait_seconds:
                time.sleep(wait_seconds)

    raise RuntimeError("unreachable retry state")


def emit_dry_run(target: dict[str, Any], parsed: dict[str, Any]) -> None:
    payload = {
        "scholarship_id": target.get("scholarship_id"),
        "notice_title": target.get("notice_title"),
        "parsed": parsed,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace") + b"\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LLM parser for Kangwon scholarship notices")
    parser.add_argument("--limit", type=int, default=None, help="Max notices to process")
    parser.add_argument("--dry-run", action="store_true", help="Call Gemini and print without DB writes")
    parser.add_argument("--reprocess", action="store_true", help="Include notices already saved in notice_llm")
    parser.add_argument("--sleep", type=float, default=config.DEFAULT_SLEEP_SECONDS, help="Delay between notices")
    parser.add_argument("--retries", type=int, default=2, help="Retries per notice when Gemini/API calls fail")
    parser.add_argument("--retry-wait", type=float, default=20, help="Base retry wait in seconds")
    return parser.parse_args()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    total = run(
        limit=args.limit,
        dry_run=args.dry_run,
        reprocess=args.reprocess,
        sleep=args.sleep,
        retries=args.retries,
        retry_wait=args.retry_wait,
    )
    logger.info("Total processed: %s", total)
