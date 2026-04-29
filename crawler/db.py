"""MySQL persistence layer for scholarship notices."""

from __future__ import annotations

from typing import Any

import mysql.connector
from mysql.connector import Error

try:
    from . import config
except ImportError:  # Allows running crawler.py directly.
    import config  # type: ignore


UPSERT_SQL = """
INSERT INTO scholarship (
    title,
    organization,
    scholarship_type,
    benefit_type,
    amount_text,
    campus_text,
    apply_start_date,
    apply_end_date,
    selection_period_text,
    eligibility_text,
    selection_criteria_text,
    application_method_text,
    detail_url,
    source_site,
    status
) VALUES (
    %(title)s,
    %(organization)s,
    %(scholarship_type)s,
    %(benefit_type)s,
    %(amount_text)s,
    %(campus_text)s,
    %(apply_start_date)s,
    %(apply_end_date)s,
    %(selection_period_text)s,
    %(eligibility_text)s,
    %(selection_criteria_text)s,
    %(application_method_text)s,
    %(detail_url)s,
    %(source_site)s,
    %(status)s
)
ON DUPLICATE KEY UPDATE
    scholarship_id = LAST_INSERT_ID(scholarship_id),
    title = VALUES(title),
    organization = VALUES(organization),
    scholarship_type = VALUES(scholarship_type),
    benefit_type = VALUES(benefit_type),
    amount_text = VALUES(amount_text),
    campus_text = VALUES(campus_text),
    apply_start_date = VALUES(apply_start_date),
    apply_end_date = VALUES(apply_end_date),
    selection_period_text = VALUES(selection_period_text),
    eligibility_text = VALUES(eligibility_text),
    selection_criteria_text = VALUES(selection_criteria_text),
    application_method_text = VALUES(application_method_text),
    source_site = VALUES(source_site),
    status = VALUES(status);
"""

CONDITION_UPSERT_SQL = """
INSERT INTO scholarship_condition (
    scholarship_id,
    grade_min,
    grade_max,
    gpa_min,
    credit_min,
    income_level_min,
    income_level_max,
    is_new_student,
    is_enrolled_student,
    is_transfer_student,
    is_foreign_student,
    department_text,
    raw_condition_text
) VALUES (
    %(scholarship_id)s,
    %(grade_min)s,
    %(grade_max)s,
    %(gpa_min)s,
    %(credit_min)s,
    %(income_level_min)s,
    %(income_level_max)s,
    %(is_new_student)s,
    %(is_enrolled_student)s,
    %(is_transfer_student)s,
    %(is_foreign_student)s,
    %(department_text)s,
    %(raw_condition_text)s
)
ON DUPLICATE KEY UPDATE
    grade_min = VALUES(grade_min),
    grade_max = VALUES(grade_max),
    gpa_min = VALUES(gpa_min),
    credit_min = VALUES(credit_min),
    income_level_min = VALUES(income_level_min),
    income_level_max = VALUES(income_level_max),
    is_new_student = VALUES(is_new_student),
    is_enrolled_student = VALUES(is_enrolled_student),
    is_transfer_student = VALUES(is_transfer_student),
    is_foreign_student = VALUES(is_foreign_student),
    department_text = VALUES(department_text),
    raw_condition_text = VALUES(raw_condition_text);
"""


def get_connection():
    """Create a MySQL connection using config.py environment values."""
    try:
        return mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            charset=config.DB_CHARSET,
        )
    except Error as exc:
        raise RuntimeError(f"MySQL connection failed: {exc}") from exc


def upsert_scholarship(connection, scholarship: dict[str, Any]) -> int:
    """Insert a scholarship and its parsed condition, then return its id."""
    payload = _scholarship_payload(scholarship)
    condition = scholarship.get("condition")
    cursor = connection.cursor()

    try:
        cursor.execute(UPSERT_SQL, payload)
        scholarship_id = int(cursor.lastrowid)

        if condition:
            condition_payload = _condition_payload(scholarship_id, condition)
            cursor.execute(CONDITION_UPSERT_SQL, condition_payload)

        connection.commit()
        return scholarship_id
    except Error as exc:
        connection.rollback()
        raise RuntimeError(f"Failed to save scholarship: {exc}") from exc
    finally:
        cursor.close()


def _scholarship_payload(scholarship: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "title",
        "organization",
        "scholarship_type",
        "benefit_type",
        "amount_text",
        "campus_text",
        "apply_start_date",
        "apply_end_date",
        "selection_period_text",
        "eligibility_text",
        "selection_criteria_text",
        "application_method_text",
        "detail_url",
        "source_site",
        "status",
    ]
    return {key: scholarship.get(key) for key in keys}


def _condition_payload(scholarship_id: int, condition: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "grade_min",
        "grade_max",
        "gpa_min",
        "credit_min",
        "income_level_min",
        "income_level_max",
        "is_new_student",
        "is_enrolled_student",
        "is_transfer_student",
        "is_foreign_student",
        "department_text",
        "raw_condition_text",
    ]
    payload = {key: condition.get(key) for key in keys}
    payload["scholarship_id"] = scholarship_id
    return payload

