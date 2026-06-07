"""Tests for llm.llm_parser module."""

import json
import pytest

from llm.llm_parser import (
    extract_json_object,
    has_explicit_grade_condition,
    infer_grade_range_from_explicit_grade_text,
    infer_grade_range_from_semester_completion,
    is_valid_grade,
    normalize_date,
    normalize_float,
    normalize_int,
    normalize_text,
    parse_response,
    validate_contest_payload,
    validate_payload,
)


# ---------------------------------------------------------------------------
# extract_json_object
# ---------------------------------------------------------------------------

class TestExtractJsonObject:
    def test_plain_json(self):
        assert extract_json_object('{"a": 1}') == '{"a": 1}'

    def test_fenced_json(self):
        result = extract_json_object('```json\n{"a": 1}\n```')
        assert result == '{"a": 1}'

    def test_fenced_no_lang(self):
        result = extract_json_object('```\n{"x": 2}\n```')
        assert result == '{"x": 2}'

    def test_embedded_json(self):
        result = extract_json_object('some text {"key": "value"} more text')
        assert result == '{"key": "value"}'

    def test_no_json_raises(self):
        with pytest.raises(ValueError):
            extract_json_object("no json here")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            extract_json_object("")

    def test_none_raises(self):
        with pytest.raises(ValueError):
            extract_json_object(None)

    def test_end_before_start_raises(self):
        with pytest.raises(ValueError):
            extract_json_object("} something {")

    def test_json_with_trailing_text(self):
        # rfind("}") returns position 1; mutant (end==+1) incorrectly raises here
        assert extract_json_object("{} trailing text") == "{}"


# ---------------------------------------------------------------------------
# parse_response
# ---------------------------------------------------------------------------

class TestParseResponse:
    def test_notice_target(self):
        payload = json.dumps({"summary": "장학금 안내"})
        result = parse_response(payload)
        assert result["summary"] == "장학금 안내"

    def test_contest_target(self):
        payload = json.dumps({"summary": "공모전 안내"})
        result = parse_response(payload, target="contest")
        assert result == {"summary": "공모전 안내"}

    def test_invalid_json_raises(self):
        with pytest.raises(Exception):
            parse_response("not json")

    def test_non_object_raises(self):
        with pytest.raises(ValueError):
            parse_response("[1, 2, 3]")


# ---------------------------------------------------------------------------
# validate_contest_payload
# ---------------------------------------------------------------------------

class TestValidateContestPayload:
    def test_returns_only_summary(self):
        result = validate_contest_payload({"summary": "공모전", "extra": "ignored"})
        assert result == {"summary": "공모전"}

    def test_none_summary(self):
        result = validate_contest_payload({})
        assert result == {"summary": None}


# ---------------------------------------------------------------------------
# normalize_text
# ---------------------------------------------------------------------------

class TestNormalizeText:
    def test_none_returns_none(self):
        assert normalize_text(None) is None

    def test_collapses_whitespace(self):
        assert normalize_text("  hello   world  ") == "hello world"

    def test_empty_string_returns_none(self):
        assert normalize_text("") is None

    def test_whitespace_only_returns_none(self):
        assert normalize_text("   ") is None

    def test_int_converted_to_str(self):
        assert normalize_text(42) == "42"

    def test_newline_collapsed(self):
        assert normalize_text("a\nb") == "a b"


# ---------------------------------------------------------------------------
# normalize_int
# ---------------------------------------------------------------------------

class TestNormalizeInt:
    def test_none_returns_none(self):
        assert normalize_int(None) is None

    def test_empty_string_returns_none(self):
        assert normalize_int("") is None

    def test_bool_returns_none(self):
        assert normalize_int(True) is None
        assert normalize_int(False) is None

    def test_int(self):
        assert normalize_int(3) == 3

    def test_float(self):
        assert normalize_int(3.9) == 3

    def test_string_number(self):
        assert normalize_int("5") == 5

    def test_string_with_digits(self):
        assert normalize_int("grade 2") == 2

    def test_no_digits_returns_none(self):
        assert normalize_int("abc") is None


# ---------------------------------------------------------------------------
# normalize_float
# ---------------------------------------------------------------------------

class TestNormalizeFloat:
    def test_none_returns_none(self):
        assert normalize_float(None) is None

    def test_empty_string_returns_none(self):
        assert normalize_float("") is None

    def test_bool_returns_none(self):
        assert normalize_float(True) is None

    def test_float_value(self):
        assert normalize_float(3.5) == 3.5

    def test_int_to_float(self):
        assert normalize_float(4) == 4.0

    def test_string_float(self):
        assert normalize_float("3.5") == 3.5

    def test_string_with_float(self):
        assert normalize_float("GPA 3.5 or higher") == 3.5

    def test_no_number_returns_none(self):
        assert normalize_float("abc") is None


# ---------------------------------------------------------------------------
# is_valid_grade
# ---------------------------------------------------------------------------

class TestIsValidGrade:
    def test_none_is_invalid(self):
        assert is_valid_grade(None) is False

    def test_zero_is_invalid(self):
        assert is_valid_grade(0) is False

    def test_six_is_invalid(self):
        assert is_valid_grade(6) is False

    def test_negative_is_invalid(self):
        assert is_valid_grade(-1) is False

    def test_one_is_valid(self):
        assert is_valid_grade(1) is True

    def test_five_is_valid(self):
        assert is_valid_grade(5) is True

    def test_three_is_valid(self):
        assert is_valid_grade(3) is True


# ---------------------------------------------------------------------------
# has_explicit_grade_condition
# ---------------------------------------------------------------------------

class TestHasExplicitGradeCondition:
    def test_none_returns_false(self):
        assert has_explicit_grade_condition(None) is False

    def test_empty_returns_false(self):
        assert has_explicit_grade_condition("") is False

    def test_jaehagsaeng(self):
        assert has_explicit_grade_condition("재학생") is True

    def test_jaehagjung(self):
        assert has_explicit_grade_condition("재학중") is True

    def test_all_grades(self):
        assert has_explicit_grade_condition("전체학년") is True
        assert has_explicit_grade_condition("모든학년") is True

    def test_specific_grade(self):
        assert has_explicit_grade_condition("2학년") is True

    def test_grade_range(self):
        assert has_explicit_grade_condition("2~4학년") is True

    def test_semester_only(self):
        assert has_explicit_grade_condition("4학기 이상") is False

    def test_unrelated_text(self):
        assert has_explicit_grade_condition("성적 우수자") is False

    def test_grade_condition_with_internal_whitespace(self):
        # Whitespace stripping is required; wrong-regex mutants keep the space
        assert has_explicit_grade_condition("전 학년") is True
        assert has_explicit_grade_condition("2 학년") is True


# ---------------------------------------------------------------------------
# infer_grade_range_from_explicit_grade_text
# ---------------------------------------------------------------------------

class TestInferGradeRangeFromExplicitGradeText:
    def test_none_returns_none_none(self):
        assert infer_grade_range_from_explicit_grade_text(None) == (None, None)

    def test_empty_returns_none_none(self):
        assert infer_grade_range_from_explicit_grade_text("") == (None, None)

    def test_jaehagsaeng(self):
        assert infer_grade_range_from_explicit_grade_text("재학생") == (1, 4)

    def test_jaehagjung(self):
        assert infer_grade_range_from_explicit_grade_text("재학중") == (1, 4)

    def test_all_grades(self):
        assert infer_grade_range_from_explicit_grade_text("전체학년") == (1, 4)

    def test_grade_range_tilde(self):
        assert infer_grade_range_from_explicit_grade_text("2~4학년") == (2, 4)

    def test_grade_range_dash(self):
        assert infer_grade_range_from_explicit_grade_text("1-3학년") == (1, 3)

    def test_grade_range_reversed(self):
        assert infer_grade_range_from_explicit_grade_text("4~2학년") == (2, 4)

    def test_single_grade(self):
        assert infer_grade_range_from_explicit_grade_text("3학년") == (3, 3)

    def test_multiple_grades(self):
        assert infer_grade_range_from_explicit_grade_text("1학년 또는 3학년") == (1, 3)

    def test_no_grade_text(self):
        assert infer_grade_range_from_explicit_grade_text("성적 우수자") == (None, None)

    def test_infer_with_internal_whitespace(self):
        # Whitespace stripping collapses "전 학년" → "전학년" before pattern matching
        assert infer_grade_range_from_explicit_grade_text("전 학년") == (1, 4)
        assert infer_grade_range_from_explicit_grade_text("2 학년") == (2, 2)


# ---------------------------------------------------------------------------
# infer_grade_range_from_semester_completion
# ---------------------------------------------------------------------------

class TestInferGradeRangeFromSemesterCompletion:
    def test_none_returns_none_none(self):
        assert infer_grade_range_from_semester_completion(None) == (None, None)

    def test_empty_returns_none_none(self):
        assert infer_grade_range_from_semester_completion("") == (None, None)

    def test_no_semester_text(self):
        assert infer_grade_range_from_semester_completion("전체학년") == (None, None)

    def test_one_semester(self):
        # semesters < 2 → grade_min = 1
        assert infer_grade_range_from_semester_completion("1학기 이상") == (1, 4)

    def test_two_semesters(self):
        # semesters=2 → grade_min = min(max(2//2+1,1),4) = 2
        assert infer_grade_range_from_semester_completion("2학기 이상") == (2, 4)

    def test_four_semesters(self):
        # semesters=4 → grade_min = min(max(4//2+1,1),4) = 3
        assert infer_grade_range_from_semester_completion("4학기 이상") == (3, 4)

    def test_six_semesters(self):
        # semesters=6 → grade_min = min(max(6//2+1,1),4) = 4
        assert infer_grade_range_from_semester_completion("6학기 이상") == (4, 4)

    def test_isusu_variant(self):
        assert infer_grade_range_from_semester_completion("4학기이수") == (3, 4)

    def test_sulyeo_variant(self):
        assert infer_grade_range_from_semester_completion("2학기수료") == (2, 4)

    def test_odd_semester_count(self):
        # Kills mutmut_36: // vs / differ for odd values (3//2=1 vs 3/2=1.5)
        assert infer_grade_range_from_semester_completion("3학기 이상") == (2, 4)
        assert infer_grade_range_from_semester_completion("5학기 이상") == (3, 4)

    def test_eight_semesters_clamped_to_four(self):
        # Kills mutmut_40: min(...,4) vs min(...,5) — 8 semesters → (8//2)+1=5 → clamp to 4
        assert infer_grade_range_from_semester_completion("8학기 이상") == (4, 4)


# ---------------------------------------------------------------------------
# normalize_date
# ---------------------------------------------------------------------------

class TestNormalizeDate:
    def test_valid_date(self):
        assert normalize_date("2025-03-01") == "2025-03-01"

    def test_none_returns_none(self):
        assert normalize_date(None) is None

    def test_wrong_format_returns_none(self):
        assert normalize_date("2025/03/01") is None

    def test_invalid_date_returns_none(self):
        assert normalize_date("2025-13-01") is None

    def test_partial_date_returns_none(self):
        assert normalize_date("2025-03") is None

    def test_empty_returns_none(self):
        assert normalize_date("") is None

    def test_whitespace_trimmed(self):
        assert normalize_date("  2025-03-01  ") == "2025-03-01"


# ---------------------------------------------------------------------------
# validate_payload integration
# ---------------------------------------------------------------------------

class TestValidatePayload:
    def test_all_none_on_empty(self):
        result = validate_payload({})
        assert result["summary"] is None
        assert result["grade_min"] is None
        assert result["grade_max"] is None
        assert result["gpa_min"] is None
        assert result["application_start_date"] is None
        assert result["application_close_date"] is None

    def test_gpa_valid_range(self):
        result = validate_payload({"gpa_min": 3.5})
        assert result["gpa_min"] == 3.5

    def test_gpa_above_max_rejected(self):
        result = validate_payload({"gpa_min": 5.0})
        assert result["gpa_min"] is None

    def test_gpa_below_min_rejected(self):
        result = validate_payload({"gpa_min": -0.1})
        assert result["gpa_min"] is None

    def test_gpa_zero_accepted(self):
        result = validate_payload({"gpa_min": 0.0})
        assert result["gpa_min"] == 0.0

    def test_gpa_4_5_accepted(self):
        result = validate_payload({"gpa_min": 4.5})
        assert result["gpa_min"] == 4.5

    def test_raw_grade_without_grade_text_overridden_to_none(self):
        # Without grade_text, semester fallback runs and returns (None,None),
        # so raw grade_min/grade_max values are discarded.
        result = validate_payload({"grade_min": 4, "grade_max": 2})
        assert result["grade_min"] is None
        assert result["grade_max"] is None

    def test_invalid_grade_cleared(self):
        result = validate_payload({"grade_min": 0, "grade_max": 6})
        assert result["grade_min"] is None
        assert result["grade_max"] is None

    def test_deadline_fallback(self):
        result = validate_payload({"deadline": "2025-12-31"})
        assert result["application_close_date"] == "2025-12-31"

    def test_explicit_grade_text_overrides_raw_grade(self):
        result = validate_payload({"grade_text": "재학생", "grade_min": 3, "grade_max": 3})
        assert result["grade_min"] == 1
        assert result["grade_max"] == 4

    def test_semester_text_sets_grade_range(self):
        result = validate_payload({"grade_text": "4학기 이상"})
        assert result["grade_min"] == 3
        assert result["grade_max"] == 4

    def test_application_start_date_returned(self):
        # Kills mutmut_60: mutation replaces normalize_date(...) with None
        result = validate_payload({"application_start_date": "2025-03-01"})
        assert result["application_start_date"] == "2025-03-01"

    def test_application_close_date_direct_key(self):
        # Kills mutmut_72: mutation changes raw.get("application_close_date") to raw.get(None)
        result = validate_payload({"application_close_date": "2025-12-31"})
        assert result["application_close_date"] == "2025-12-31"
