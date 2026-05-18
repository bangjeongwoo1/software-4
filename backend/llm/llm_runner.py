"""CLI runner for Gemini-based notice and contest parsing."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from typing import Any

from . import llm_config as config
from .llm_client import call_gemini
from .llm_db import fetch_notice_targets, fetch_contest_targets, save_notice_llm, save_contest_llm


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run(
    *,
    target: str = "notice",
    limit: int | None = None,
    dry_run: bool = False,
    reprocess: bool = False,
    sleep: float = config.DEFAULT_SLEEP_SECONDS,
    retries: int = 2,
    retry_wait: float = 20,
) -> int:
    """Process notice_detail_2 or contest_detail_2 rows through Gemini."""

    if limit is not None and limit < 1:
        raise ValueError("limit must be >= 1")
    if sleep < 0:
        raise ValueError("sleep must be >= 0")
    if retries < 0:
        raise ValueError("retries must be >= 0")
    if retry_wait < 0:
        raise ValueError("retry_wait must be >= 0")

    if target == "notice":
        targets = fetch_notice_targets(limit=limit, reprocess=reprocess)
        id_key = "scholarship_id"
        title_key = "notice_title"
    else:
        targets = fetch_contest_targets(limit=limit, reprocess=reprocess)
        id_key = "contest_id"
        title_key = "contest_title"

    logger.info("Loaded %s %s target(s)", len(targets), target)

    processed = 0
    for index, target_row in enumerate(targets):
        item_id = target_row[id_key]
        logger.info("Processing %s=%s", id_key, item_id)
        try:
            parsed = call_gemini_with_retries(
                target_row, target=target, retries=retries, retry_wait=retry_wait
            )
        except Exception as exc:
            logger.exception("Skipping %s=%s after LLM failure: %s", id_key, item_id, exc)
            continue

        if dry_run:
            emit_dry_run(target_row, parsed, id_key=id_key, title_key=title_key, target=target)
        elif target == "notice":
            save_notice_llm(
                scholarship_id=item_id,
                notice_title=target_row.get(title_key),
                parsed=parsed,
            )
        else:
            save_contest_llm(
                contest_id=item_id,
                contest_title=target_row.get(title_key),
                parsed=parsed,
            )
        processed += 1

        if sleep and index < len(targets) - 1:
            time.sleep(sleep)

    failed = len(targets) - processed
    logger.info("LLM %s parsing complete. Processed %s item(s), failed %s item(s)", target, processed, failed)
    return processed


def call_gemini_with_retries(
    target_row: dict[str, Any], *, target: str, retries: int, retry_wait: float
) -> dict[str, Any]:
    """Call Gemini with simple retries for transient API errors."""

    id_key = "scholarship_id" if target == "notice" else "contest_id"
    item_id = target_row.get(id_key)
    for attempt in range(retries + 1):
        try:
            return call_gemini(
                raw_text=target_row.get("raw_text"),
                image_url=target_row.get("image_file_url") if target == "notice" else None,
                pdf_url=target_row.get("attachment_file_url") if target == "notice" else None,
                prompt_type=target,
            )
        except Exception:
            if attempt >= retries:
                raise
            wait_seconds = retry_wait * (attempt + 1)
            logger.warning(
                "Gemini call failed for %s=%s. Retrying %s/%s after %.1fs",
                id_key,
                item_id,
                attempt + 1,
                retries,
                wait_seconds,
                exc_info=True,
            )
            if wait_seconds:
                time.sleep(wait_seconds)

    raise RuntimeError("unreachable retry state")


def emit_dry_run(
    target_row: dict[str, Any],
    parsed: dict[str, Any],
    *,
    id_key: str,
    title_key: str,
    target: str,
) -> None:
    payload = {
        "target": target,
        id_key: target_row.get(id_key),
        title_key: target_row.get(title_key),
        "parsed": parsed,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace") + b"\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LLM parser for Kangwon scholarship notices and contests")
    parser.add_argument(
        "--target",
        choices=("notice", "contest"),
        default="notice",
        help="LLM target type: notice or contest",
    )
    parser.add_argument("--limit", type=int, default=None, help="Max items to process")
    parser.add_argument("--dry-run", action="store_true", help="Call Gemini and print without DB writes")
    parser.add_argument("--reprocess", action="store_true", help="Include items already saved in the output table")
    parser.add_argument("--sleep", type=float, default=config.DEFAULT_SLEEP_SECONDS, help="Delay between items")
    parser.add_argument("--retries", type=int, default=2, help="Retries per item when Gemini/API calls fail")
    parser.add_argument("--retry-wait", type=float, default=20, help="Base retry wait in seconds")
    return parser.parse_args()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    total = run(
        target=args.target,
        limit=args.limit,
        dry_run=args.dry_run,
        reprocess=args.reprocess,
        sleep=args.sleep,
        retries=args.retries,
        retry_wait=args.retry_wait,
    )
    logger.info("Total processed: %s", total)
