"""Parsing helpers for Kangwon scholarship pages."""

from __future__ import annotations

import re
from datetime import date
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

try:
    from . import config
except ImportError:  # Allows running crawler.py directly.
    import config  # type: ignore


LABEL_ORGANIZATION = [
    "\uae30\uad00",
    "\uc8fc\uad00",
    "\uc6b4\uc601\uae30\uad00",
    "\uc7a5\ud559\uc7ac\ub2e8",
]
LABEL_TYPE = [
    "\uc720\ud615",
    "\uad6c\ubd84",
    "\uc7a5\ud559\uae08 \uc720\ud615",
]
LABEL_AMOUNT = [
    "\uae08\uc561",
    "\uc9c0\uc6d0\uae08\uc561",
    "\uc7a5\ud559\uae08\uc561",
    "\uc9c0\uc6d0\ub0b4\uc6a9",
]

DATE_PATTERNS = [
    re.compile(r"(\d{4})[.\-/\uB144\s]+(\d{1,2})[.\-/\uC6D4\s]+(\d{1,2})"),
    re.compile(r"(\d{2})[.\-/\uB144\s]+(\d{1,2})[.\-/\uC6D4\s]+(\d{1,2})"),
]


def collect_detail_links(list_html: str, list_url: str) -> list[str]:
    """Collect unique detail page links from a list page."""
    soup = BeautifulSoup(list_html, "html.parser")

    if "/janghak/list.do" in list_url:
        return _collect_janghak_links(soup, list_url)
    if "/bbs/750/list.do" in list_url:
        return _collect_notice_links(soup, list_url)

    return _collect_generic_links(soup, list_url)


def _collect_janghak_links(soup: BeautifulSoup, list_url: str) -> list[str]:
    """Collect only scholarship detail buttons from the custom search result."""
    links: list[str] = []
    seen: set[str] = set()

    for anchor in soup.select("table tbody a[href*='detail.do'][href*='janghakSn=']"):
        href = anchor.get("href")
        if not href:
            continue

        detail_url = urljoin(list_url, href.strip())
        if detail_url in seen:
            continue

        seen.add(detail_url)
        links.append(detail_url)

    return links


def _collect_notice_links(soup: BeautifulSoup, list_url: str) -> list[str]:
    """Collect only notice detail links from the scholarship notice board."""
    links: list[str] = []
    seen: set[str] = set()

    for anchor in soup.select("table tbody a[href*='detail.do'][href*='pstSn=']"):
        href = anchor.get("href")
        if not href:
            continue

        detail_url = urljoin(list_url, href.strip())
        if detail_url in seen:
            continue

        seen.add(detail_url)
        links.append(detail_url)

    return links


def _collect_generic_links(soup: BeautifulSoup, list_url: str) -> list[str]:
    """Fallback collector for simple board pages."""
    links: list[str] = []
    seen: set[str] = set()

    for anchor in soup.select(config.LIST_LINK_SELECTOR):
        href = anchor.get("href")
        if not href:
            continue

        detail_url = urljoin(list_url, href.strip())
        if detail_url in seen:
            continue

        lowered = detail_url.lower()
        looks_like_detail = any(
            token in lowered for token in ("view", "detail", "notice", "board", "scholar")
        )
        if config.LIST_LINK_SELECTOR != "a" or looks_like_detail:
            seen.add(detail_url)
            links.append(detail_url)

    return links


def parse_detail_page(detail_html: str, detail_url: str) -> dict:
    """Extract normalized scholarship fields from a detail page."""
    soup = BeautifulSoup(detail_html, "html.parser")

    if "/janghak/detail.do" in detail_url:
        return _parse_janghak_detail(soup, detail_url)

    return _parse_notice_detail(soup, detail_url)


def _parse_janghak_detail(soup: BeautifulSoup, detail_url: str) -> dict:
    fields = _extract_ans_fields(soup)
    title = fields.get("\uc7a5\ud559\uba85", "")
    summary = fields.get("\uac1c\uc694")
    scholarship_type = fields.get("\uc7a5\ud559\uad6c\ubd84")
    benefit_type = fields.get("\uc7a5\ud559\uc131\uaca9")
    amount_text = fields.get("\uc7a5\ud559\uae08\uc561")
    eligibility_text = fields.get("\uc218\ud61c\uc790\uaca9") or summary
    selection_period_text = fields.get("\uc120\ubc1c\uc2dc\uae30")
    application_method_text = fields.get("\uc81c\ucd9c\ubc29\ubc95")
    campus_text = fields.get("\ucea0\ud37c\uc2a4")
    content_text = _clean_text(" ".join(value for value in fields.values() if value))
    start_date, end_date = _extract_period(content_text)
    condition_source = _join_condition_sources(eligibility_text, content_text)
    condition = _extract_condition(condition_source)

    return {
        "title": title,
        "organization": "\uac15\uc6d0\ub300\ud559\uad50",
        "scholarship_type": scholarship_type,
        "benefit_type": benefit_type,
        "amount_text": amount_text,
        "campus_text": campus_text,
        "apply_start_date": start_date,
        "apply_end_date": end_date,
        "selection_period_text": selection_period_text,
        "eligibility_text": eligibility_text or content_text[:1000],
        "selection_criteria_text": summary,
        "application_method_text": application_method_text,
        "detail_url": detail_url,
        "source_site": "kangwon_janghak",
        "status": _status_from_dates(start_date, end_date),
        "condition": condition,
    }


def _parse_notice_detail(soup: BeautifulSoup, detail_url: str) -> dict:
    meta = _extract_notice_meta(soup)
    full_text = _clean_text(soup.get_text(" ", strip=True))
    content_text = _extract_content_text(soup)

    title = _extract_title(soup) or _guess_title_from_text(content_text or full_text)
    organization = meta.get("author") or _extract_labeled_value(content_text, LABEL_ORGANIZATION)
    scholarship_type = _extract_labeled_value(content_text, LABEL_TYPE) or _infer_scholarship_type(
        title,
        content_text,
    )
    amount_text = _extract_amount(content_text)
    start_date, end_date = _extract_period(content_text)
    eligibility_text = _extract_eligibility(content_text) or content_text[:1000]

    return {
        "title": title,
        "organization": organization,
        "scholarship_type": scholarship_type,
        "benefit_type": None,
        "amount_text": amount_text,
        "campus_text": None,
        "apply_start_date": start_date,
        "apply_end_date": end_date,
        "selection_period_text": None,
        "eligibility_text": eligibility_text,
        "selection_criteria_text": None,
        "application_method_text": None,
        "detail_url": detail_url,
        "source_site": "kangwon_notice",
        "status": _status_from_dates(start_date, end_date),
        "condition": _extract_condition(_join_condition_sources(eligibility_text, content_text)),
    }


def _join_condition_sources(*values: Optional[str]) -> str:
    return _clean_text(" ".join(value for value in values if value))


def _extract_ans_fields(soup: BeautifulSoup) -> dict[str, str]:
    fields: dict[str, str] = {}
    container = soup.select_one(".sub-contents-container.detail > .card.detail")
    search_root = container if container else soup

    for field in search_root.select(".ans-field"):
        label = field.select_one(".ans-field-label")
        value = field.select_one(".ans-field-value")
        if not label or not value:
            continue

        key = _clean_text(label.get_text(" ", strip=True))
        text = _clean_text(value.get_text(" ", strip=True))
        if key and text:
            fields[key] = text

    return fields


def _extract_title(soup: BeautifulSoup) -> str:
    title = soup.select_one(".card-header h3.heading-02")
    if title:
        text = _clean_text(title.get_text(" ", strip=True))
        if text and text != "\uc7a5\ud559\uae08 \uc0c1\uc138":
            return text

    title_node = soup.select_one(config.TITLE_SELECTOR)
    if title_node:
        return _clean_text(title_node.get_text(" ", strip=True))

    if soup.title and soup.title.string:
        return _clean_text(soup.title.string)

    return ""


def _extract_content_text(soup: BeautifulSoup) -> str:
    content = soup.select_one(".info-editor-area .editor-wrap")
    if content:
        return _clean_text(content.get_text(" ", strip=True))

    content_node = soup.select_one(config.CONTENT_SELECTOR)
    if content_node:
        return _clean_text(content_node.get_text(" ", strip=True))
    return _clean_text(soup.get_text(" ", strip=True))


def _guess_title_from_text(text: str) -> str:
    return text[:120]


def _extract_labeled_value(text: str, labels: list[str]) -> Optional[str]:
    for label in labels:
        pattern = re.compile(rf"{re.escape(label)}\s*[:\uFF1A]\s*([^|/\n\r]+?)(?=\s{{2,}}|$)")
        match = pattern.search(text)
        if match:
            return _clean_text(match.group(1))[:255]
    return None


def _extract_notice_meta(soup: BeautifulSoup) -> dict[str, str]:
    meta: dict[str, str] = {}

    for row in soup.select(".table.table-row tr"):
        header = row.find("th")
        value = row.find("td")
        if not header or not value:
            continue

        key = _clean_text(header.get_text(" ", strip=True))
        text = _clean_text(value.get_text(" ", strip=True))
        if key == "\uc791\uc131\uc790":
            meta["author"] = text
        elif key == "\ubb38\uc758\uc804\ud654":
            meta["phone"] = text

    return meta


def _infer_scholarship_type(title: str, text: str) -> Optional[str]:
    source = f"{title} {text}"
    if "\ud559\uc790\uae08\ub300\ucd9c" in source:
        return "\ud559\uc790\uae08\ub300\ucd9c"
    if "\uad6d\uac00\uc7a5\ud559" in source or "\ud55c\uad6d\uc7a5\ud559\uc7ac\ub2e8" in source:
        return "\uad6d\uac00\uc7a5\ud559"
    if "\uad50\uc678" in source:
        return "\uad50\uc678\uc7a5\ud559"
    if "\uad50\ub0b4" in source or "KNU" in source:
        return "\uad50\ub0b4\uc7a5\ud559"
    return None


def _extract_amount(text: str) -> Optional[str]:
    labeled = _extract_labeled_value(text, LABEL_AMOUNT)
    if labeled:
        return labeled[:255]

    match = re.search(
        r"((?:\d{1,3}(?:,\d{3})*|\d+)\s*(?:\uC6D0|\uB9CC\uC6D0|\uCC9C\uC6D0))",
        text,
    )
    return match.group(1) if match else None


def _extract_condition(text: str) -> dict:
    """Extract searchable condition hints from Korean eligibility text."""
    cleaned = _clean_text(text)
    return {
        "grade_min": _extract_grade_min(cleaned),
        "grade_max": _extract_grade_max(cleaned),
        "gpa_min": _extract_gpa_min(cleaned),
        "credit_min": _extract_credit_min(cleaned),
        "income_level_min": _extract_income_min(cleaned),
        "income_level_max": _extract_income_max(cleaned),
        "is_new_student": _contains_any(cleaned, ["\uc2e0\uc785\uc0dd", "\uc785\ud559\uc608\uc815\uc790"]),
        "is_enrolled_student": _contains_any(
            cleaned,
            ["\uc7ac\ud559\uc0dd", "\uc7ac\ud559 \uc911", "\uc7ac\ud559\uc911", "\uc7ac\ud559 \uc608\uc815", "\uc7ac\ud559\uc73c\ub85c"],
        ),
        "is_transfer_student": _contains_any(cleaned, ["\ud3b8\uc785\uc0dd"]),
        "is_foreign_student": _contains_any(cleaned, ["\uc678\uad6d\uc778", "\uc720\ud559\uc0dd"]),
        "department_text": _extract_department_text(cleaned),
        "raw_condition_text": cleaned[:2000],
    }


def _extract_grade_min(text: str) -> Optional[int]:
    range_match = re.search(r"([1-6])\s*~\s*([1-6])\s*\ud559\ub144", text)
    if range_match:
        return int(range_match.group(1))

    min_match = re.search(r"([1-6])\s*\ud559\ub144\s*(?:\uc774\uc0c1|\ubd80\ud130)", text)
    if min_match:
        return int(min_match.group(1))

    single_match = re.search(r"([1-6])\s*\ud559\ub144", text)
    if single_match:
        return int(single_match.group(1))
    return None


def _extract_grade_max(text: str) -> Optional[int]:
    range_match = re.search(r"([1-6])\s*~\s*([1-6])\s*\ud559\ub144", text)
    if range_match:
        return int(range_match.group(2))

    max_match = re.search(r"([1-6])\s*\ud559\ub144\s*(?:\uc774\ud558|\uae4c\uc9c0)", text)
    if max_match:
        return int(max_match.group(1))

    single_match = re.search(r"([1-6])\s*\ud559\ub144", text)
    if single_match:
        return int(single_match.group(1))
    return None


def _extract_gpa_min(text: str) -> Optional[float]:
    match = re.search(
        r"(?:\ud3c9\uc810\ud3c9\uade0|\ud3c9\uc810|\ud559\uc810|GPA).{0,30}?"
        r"([0-4](?:\.\d{1,2})?)\s*(?:\ud559\uc810|\uc810|/4\.5|/4\.3)?\s*(?:\uc774\uc0c1|\ucd08\uacfc)",
        text,
        re.IGNORECASE,
    )
    if match:
        return float(match.group(1))
    return None


def _extract_credit_min(text: str) -> Optional[int]:
    match = re.search(r"(\d{1,3})\s*\ud559\uc810\s*(?:\uc774\uc0c1|\ucd08\uacfc)", text)
    if match:
        return int(match.group(1))
    return None


def _extract_income_min(text: str) -> Optional[int]:
    range_match = re.search(
        r"([0-9]|10)\s*(?:\ubd84\uc704|\uad6c\uac04)?"
        r"(?:[\(\uFF08][^\)\uFF09]*[\)\uFF09])?\s*[~\-]\s*"
        r"([0-9]|10)\s*(?:\ubd84\uc704|\uad6c\uac04)",
        text,
    )
    if range_match:
        return int(range_match.group(1))

    min_match = re.search(r"([0-9]|10)\s*(?:\ubd84\uc704|\uad6c\uac04)\s*(?:\uc774\uc0c1|\ucd08\uacfc)", text)
    if min_match:
        return int(min_match.group(1))
    listed_levels = _extract_listed_income_levels(text)
    if listed_levels:
        return min(listed_levels)
    if _contains_any(text, ["\uae30\ucd08", "\ucc28\uc0c1\uc704"]):
        return 0
    return None


def _extract_income_max(text: str) -> Optional[int]:
    range_match = re.search(
        r"([0-9]|10)\s*(?:\ubd84\uc704|\uad6c\uac04)?"
        r"(?:[\(\uFF08][^\)\uFF09]*[\)\uFF09])?\s*[~\-]\s*"
        r"([0-9]|10)\s*(?:\ubd84\uc704|\uad6c\uac04)",
        text,
    )
    if range_match:
        return int(range_match.group(2))

    max_match = re.search(r"([0-9]|10)\s*(?:\ubd84\uc704|\uad6c\uac04)\s*(?:\uc774\ud558|\uae4c\uc9c0)", text)
    if max_match:
        return int(max_match.group(1))
    listed_levels = _extract_listed_income_levels(text)
    if listed_levels:
        return max(listed_levels)
    return None


def _extract_listed_income_levels(text: str) -> list[int]:
    """Extract income levels written as repeated values, e.g. 0구간, 1구간, 2구간."""
    if not re.search(r"(?:\uc18c\ub4dd|\ud559\uc790\uae08\uc9c0\uc6d0|\ubd84\uc704|\uad6c\uac04)", text):
        return []

    levels = [
        int(match)
        for match in re.findall(r"(?<!\d)([0-9]|10)\s*(?:\ubd84\uc704|\uad6c\uac04)(?!\d)", text)
    ]
    return sorted(set(levels))


def _extract_department_text(text: str) -> Optional[str]:
    match = re.search(r"([\w\s\uAC00-\uD7A3]+(?:\ud559\uacfc|\ub2e8\uacfc\ub300\ud559|\ub300\ud559))", text)
    if match:
        return _clean_text(match.group(1))[:255]
    return None


def _contains_any(text: str, keywords: list[str]) -> Optional[bool]:
    return True if any(keyword in text for keyword in keywords) else None


def _extract_period(text: str) -> tuple[Optional[date], Optional[date]]:
    period_match = re.search(
        r"((?:\d{2,4}[.\-/\uB144\s]+\d{1,2}[.\-/\uC6D4\s]+\d{1,2}).{0,20}?"
        r"(?:~|-|\uBD80\uD130|\uAE4C\uC9C0).{0,20}?"
        r"(?:\d{2,4}[.\-/\uB144\s]+\d{1,2}[.\-/\uC6D4\s]+\d{1,2}))",
        text,
    )
    if period_match:
        dates = _parse_dates(period_match.group(1))
        if len(dates) >= 2:
            return dates[0], dates[1]

    dates = _parse_dates(text)
    if len(dates) >= 2:
        return dates[0], dates[1]
    if len(dates) == 1:
        return None, dates[0]
    return None, None


def _parse_dates(text: str) -> list[date]:
    parsed: list[date] = []
    for pattern in DATE_PATTERNS:
        for year_text, month_text, day_text in pattern.findall(text):
            year = int(year_text)
            if year < 100:
                year += 2000
            try:
                parsed.append(date(year, int(month_text), int(day_text)))
            except ValueError:
                continue
    return parsed


def _extract_eligibility(text: str) -> Optional[str]:
    match = re.search(
        r"(?:"
        r"\uc9c0\uc6d0\s*\uc790\uaca9|"
        r"\uc2e0\uccad\s*\uc790\uaca9|"
        r"\uc790\uaca9\s*\uae30\uc900|"
        r"\uc120\ubc1c\s*\ub300\uc0c1|"
        r"\uc2e0\uccad\s*\ub300\uc0c1|"
        r"\uc9c0\uc6d0\s*\ub300\uc0c1|"
        r"\uc790\uaca9|"
        r"\ub300\uc0c1"
        r")\s*[\)\]:\uFF1A]?\s*(.{20,1200}?)(?="
        r"\uc120\ubc1c\s*\uae30\uc900|"
        r"\uc2e0\uccad\s*\uae30\uac04|"
        r"\uc2e0\uccad\s*\ubc29\ubc95|"
        r"\uc81c\ucd9c\s*\uc11c\ub958|"
        r"\ucd94\ucc9c\s*\uae30\ud55c|"
        r"\ubb38\uc758|"
        r"$)",
        text,
    )
    if match:
        return _clean_text(match.group(1))
    return None


def _status_from_dates(start_date: Optional[date], end_date: Optional[date]) -> str:
    today = date.today()
    if end_date and end_date < today:
        return "closed"
    if start_date and start_date > today:
        return "scheduled"
    return "open"


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()
