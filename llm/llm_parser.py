"""Parsing and validation for Gemini notice extraction responses."""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Any


TEXT_FIELDS = ("summary", "amount_text", "department_text", "grade_text")
OUTPUT_FIELDS = (
    *TEXT_FIELDS,
    "grade_min",
    "grade_max",
    "gpa_min",
    "application_start_date",
    "application_close_date",
)


def parse_response(response_text: str) -> dict[str, Any]:
    """Parse Gemini JSON text and return a DB-ready validated payload."""

    raw = json.loads(extract_json_object(response_text))
    if not isinstance(raw, dict):
        raise ValueError("Gemini response must be a JSON object")
    return validate_payload(raw)


def extract_json_object(text: str) -> str:
    """Extract a single JSON object from plain or fenced Gemini output."""

    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Gemini response does not contain a JSON object")
    return text[start : end + 1]


def validate_payload(raw: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {field: None for field in OUTPUT_FIELDS}

    for field in TEXT_FIELDS:
        payload[field] = normalize_text(raw.get(field))

    grade_min = normalize_int(raw.get("grade_min"))
    grade_max = normalize_int(raw.get("grade_max"))
    if not is_valid_grade(grade_min):
        grade_min = None
    if not is_valid_grade(grade_max):
        grade_max = None
    if grade_min is not None and grade_max is not None and grade_min > grade_max:
        grade_min, grade_max = grade_max, grade_min
    payload["grade_min"] = grade_min
    payload["grade_max"] = grade_max

    gpa_min = normalize_float(raw.get("gpa_min"))
    payload["gpa_min"] = gpa_min if gpa_min is not None and 0.0 <= gpa_min <= 4.5 else None

    payload["application_start_date"] = normalize_date(raw.get("application_start_date"))
    payload["application_close_date"] = normalize_date(
        raw.get("application_close_date") or raw.get("deadline")
    )

    return payload


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value or None


def normalize_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        match = re.search(r"\d+", str(value))
        return int(match.group(0)) if match else None


def normalize_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        match = re.search(r"\d+(?:\.\d+)?", str(value))
        return float(match.group(0)) if match else None


def is_valid_grade(value: int | None) -> bool:
    return value is not None and 1 <= value <= 5


def normalize_date(value: Any) -> str | None:
    text = normalize_text(value)
    if not text or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return None
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        return None
