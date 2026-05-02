"""Parsers for the Kangwon scholarship renewal crawler."""

from __future__ import annotations

import re
from datetime import date
from pathlib import PurePosixPath
from urllib.parse import parse_qsl, urlencode, unquote, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup


VALID_STATUSES = {"open", "closed", "upcoming"}


def parse_customized_list(html: str, page_url: str) -> list[dict]:
    """Parse the customized scholarship list table."""

    soup = BeautifulSoup(html, "html.parser")
    items: list[dict] = []

    for row in soup.select("table tr"):
        cells = row.find_all("td")
        if len(cells) < 5:
            continue

        title = clean_text(cells[1].get_text(" ", strip=True))
        if not title:
            continue

        detail_url = None
        for link in row.find_all("a", href=True):
            if "janghakSn=" in link["href"]:
                detail_url = normalize_detail_url(urljoin(page_url, link["href"]))
                break

        if not detail_url:
            continue

        items.append(
            {
                "title": title,
                "scholarship_type": clean_text(cells[2].get_text(" ", strip=True)),
                "benefit_type": clean_text(cells[3].get_text(" ", strip=True)),
                "summary": clean_text(cells[4].get_text(" ", strip=True)),
                "detail_url": detail_url,
            }
        )

    return items


def parse_customized_detail(html: str, detail_url: str, list_item: dict | None = None) -> dict:
    """Parse a customized scholarship detail page."""

    soup = BeautifulSoup(html, "html.parser")
    fields = extract_kv_fields(soup)
    list_item = list_item or {}

    title = pick(fields, "장학명") or list_item.get("title")
    summary = pick(fields, "개요") or list_item.get("summary")
    grade_min, grade_max = parse_grade_range(pick(fields, "학년"))
    income_min, income_max = parse_income_range(
        pick(fields, "학자금지원구간") or pick(fields, "소득분위")
    )
    department_flags = parse_department_flags(pick(fields, "계열구분"))

    detail = {
        "title": title,
        "summary": summary,
        "campus_text": pick(fields, "캠퍼스"),
        "scholarship_type": pick(fields, "장학구분") or list_item.get("scholarship_type"),
        "benefit_type": pick(fields, "장학성격") or list_item.get("benefit_type"),
        "nationality_type": pick(fields, "국적구분"),
        "student_type": pick(fields, "학생구분"),
        "grade_min": grade_min,
        "grade_max": grade_max,
        "income_level_min": income_min,
        "income_level_max": income_max,
        "enrollment_type": pick(fields, "수업연한구분"),
        "credit_prev_value": parse_number(pick(fields, "학점(직전학기)")),
        "gpa_prev_semester_value": parse_number(pick(fields, "평점(직전학기)")),
        "gpa_total_value": parse_number(pick(fields, "총평점") or pick(fields, "총 평점")),
        "amount_text": pick(fields, "장학금액"),
        "selection_period_text": pick(fields, "선발시기"),
        "requires_recommendation": parse_recommendation(pick(fields, "추천필요여부")),
        "requires_recommendation_text": normalize_optional_text(pick(fields, "추천필요여부")),
        "selection_method_text": pick(fields, "선발방법"),
        "eligibility_text": pick(fields, "수혜자격"),
        "application_method_text": pick(fields, "제출방법"),
        "related_document_text": pick(fields, "관련문서"),
        "note_text": pick(fields, "비고"),
    }
    detail.update(department_flags)
    return detail


def parse_notice_list(html: str, page_url: str) -> list[dict]:
    """Parse the scholarship notice board list."""

    soup = BeautifulSoup(html, "html.parser")
    items: list[dict] = []

    table = find_notice_list_table(soup)
    if not table:
        return items

    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 6:
            continue

        number_text = clean_text(cells[0].get_text(" ", strip=True))
        campus = normalize_campus_text(cells[1].get_text(" ", strip=True))
        title_cell = cells[2]
        author = clean_text(cells[3].get_text(" ", strip=True)) or None
        created_at = clean_text(cells[4].get_text(" ", strip=True)) or None
        views = parse_int(cells[5].get_text(" ", strip=True))

        detail_url = None
        title = None
        for link in title_cell.find_all("a", href=True):
            if "pstSn=" in link["href"]:
                detail_url = normalize_detail_url(urljoin(page_url, link["href"]))
                title = clean_text(link.get_text(" ", strip=True))
                break

        if not detail_url or not title:
            continue

        items.append(
            {
                "is_notice": number_text == "공지",
                "campus_text": campus,
                "title": title,
                "author": author,
                "registered_at": created_at,
                "view_count": views,
                "detail_url": detail_url,
            }
        )

    return items


def parse_notice_detail(html: str, detail_url: str, list_item: dict | None = None) -> dict:
    """Parse a scholarship notice detail page."""

    soup = BeautifulSoup(html, "html.parser")
    list_item = list_item or {}

    title = list_item.get("title") or extract_title(soup)
    raw_text = extract_notice_body_text(soup)
    meta = extract_notice_meta(soup)
    attachments = extract_attachments(soup, detail_url)

    return {
        "title": title,
        "campus_text": list_item.get("campus_text") or normalize_campus_text(meta.get("campus_text")),
        "author": meta.get("author") or list_item.get("author"),
        "contact_phone": extract_phone(raw_text),
        "raw_text": raw_text,
        "attachment_file_url": "\n".join(attachments["files"]) if attachments["files"] else None,
        "attachment_file_type": ",".join(attachment_types(attachments["files"])) or None,
        "image_file_url": first_value(attachments["images"]),
    }


def extract_kv_fields(soup: BeautifulSoup) -> dict[str, str]:
    """Extract key/value fields from Kangwon detail layouts."""

    fields: dict[str, str] = {}

    for field in soup.find_all("div", class_=lambda value: value and "ans-field" in value):
        label_el = field.select_one(".ans-field-label")
        value_el = field.select_one(".ans-field-value")
        if label_el and value_el:
            key = clean_text(label_el.get_text(" ", strip=True))
            value = clean_text(value_el.get_text(" ", strip=True))
            if key and value:
                fields[key] = value

    if fields:
        return fields

    for row in soup.find_all("tr"):
        headers = row.find_all("th")
        values = row.find_all("td")
        for header, value in zip(headers, values):
            key = clean_text(header.get_text(" ", strip=True))
            text = clean_text(value.get_text(" ", strip=True))
            if key and text:
                fields[key] = text

    for dl in soup.find_all("dl"):
        terms = dl.find_all("dt")
        defs = dl.find_all("dd")
        for term, definition in zip(terms, defs):
            key = clean_text(term.get_text(" ", strip=True))
            text = clean_text(definition.get_text(" ", strip=True))
            if key and text:
                fields[key] = text

    return fields


def normalize_detail_url(url: str) -> str:
    """Keep only the identifying query parameter for stable deduplication."""

    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))

    if "janghakSn" in query:
        new_query = urlencode({"janghakSn": query["janghakSn"]})
    elif "pstSn" in query:
        new_query = urlencode({"pstSn": query["pstSn"]})
    else:
        new_query = parts.query

    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, ""))


def find_notice_list_table(soup: BeautifulSoup):
    """Find the actual BBS list table, not the search-condition table."""

    required = {"번호", "캠퍼스", "제목", "작성자", "등록일시", "조회수"}
    for table in soup.find_all("table"):
        headers = {clean_text(th.get_text(" ", strip=True)) for th in table.find_all("th")}
        if required.issubset(headers):
            return table
    return None


def normalize_campus_text(text: str | None) -> str:
    """Normalize Kangwon campus labels for notice list/detail rows."""

    cleaned = clean_text(text)
    if not cleaned:
        return "all"

    if cleaned.upper() == "ALL" or cleaned in {"전체", "전 캠퍼스", "전캠퍼스"}:
        return "all"

    campuses = []
    for campus in ("강릉", "원주", "춘천", "삼척", "도계"):
        if campus in cleaned and campus not in campuses:
            campuses.append(campus)

    if not campuses:
        return "all"
    return ",".join(campuses)


def build_status(start_date: str | None, end_date: str | None) -> str:
    """Calculate status from dates. Missing dates are treated as open."""

    today = date.today()
    start = parse_iso_date(start_date)
    end = parse_iso_date(end_date)

    if start and today < start:
        return "upcoming"
    if end and today > end:
        return "closed"
    return "open"


def extract_period(text: str | None) -> tuple[str | None, str | None]:
    """Extract a YYYY-MM-DD date range from text."""

    if not text:
        return None, None

    normalized = text.replace("년", ".").replace("월", ".").replace("일", " ")

    full = re.search(
        r"(\d{4})[.\-/]\s*(\d{1,2})[.\-/]\s*(\d{1,2})\s*(?:~|-|부터|至|까지)\s*"
        r"(\d{4})[.\-/]\s*(\d{1,2})[.\-/]\s*(\d{1,2})",
        normalized,
    )
    if full:
        return (
            format_date(full.group(1), full.group(2), full.group(3)),
            format_date(full.group(4), full.group(5), full.group(6)),
        )

    same_year = re.search(
        r"(\d{4})[.\-/]\s*(\d{1,2})[.\-/]\s*(\d{1,2})\s*(?:~|-|부터|至|까지)\s*"
        r"(\d{1,2})[.\-/]\s*(\d{1,2})",
        normalized,
    )
    if same_year:
        return (
            format_date(same_year.group(1), same_year.group(2), same_year.group(3)),
            format_date(same_year.group(1), same_year.group(4), same_year.group(5)),
        )

    single = re.search(r"(\d{4})[.\-/]\s*(\d{1,2})[.\-/]\s*(\d{1,2})", normalized)
    if single:
        return format_date(single.group(1), single.group(2), single.group(3)), None

    return None, None


def parse_grade_range(text: str | None) -> tuple[int | None, int | None]:
    """Parse grade text. Kangwon's 5th grade option is normalized to 4th grade."""

    if not text:
        return None, None

    if re.search(r"전체|제한\s*없|무관|해당\s*없", text):
        return None, None

    numbers = [int(match) for match in re.findall(r"([1-9])\s*학년", text)]
    numbers = [number for number in numbers if 1 <= number <= 4]
    if numbers:
        return min(numbers), max(numbers)

    range_match = re.search(r"([1-9])\s*(?:~|-|부터)\s*([1-9])\s*학년", text)
    if range_match:
        start = min(int(range_match.group(1)), 4)
        end = min(int(range_match.group(2)), 4)
        return min(start, end), max(start, end)

    above = re.search(r"([1-9])\s*학년\s*이상", text)
    if above:
        return min(int(above.group(1)), 4), 4

    below = re.search(r"([1-9])\s*학년\s*이하", text)
    if below:
        return 1, min(int(below.group(1)), 4)

    digits = [int(match) for match in re.findall(r"\b([1-9])\b", text)]
    digits = [number for number in digits if 1 <= number <= 4]
    if digits:
        return min(digits), max(digits)

    return None, None


def parse_income_range(text: str | None) -> tuple[int | None, int | None]:
    """Parse income level text with the md-specific 0~9 correction."""

    if not text:
        return None, None

    levels = sorted({int(match) for match in re.findall(r"(\d+)\s*구간", text)})
    if not levels:
        return None, None

    if levels == list(range(10)):
        return 0, 9
    if levels == list(range(9)):
        return 0, 8
    return min(levels), max(levels)


def parse_department_flags(text: str | None) -> dict[str, bool | None]:
    """Return boolean flags for the four department categories."""

    if not text:
        return {
            "department_humanities": None,
            "department_science": None,
            "department_engineering": None,
            "department_arts": None,
        }

    return {
        "department_humanities": True if "인문" in text else None,
        "department_science": True if "자연" in text else None,
        "department_engineering": True if "공학" in text else None,
        "department_arts": True if "예체능" in text else None,
    }


def parse_recommendation(text: str | None) -> bool | None:
    if not text:
        return None
    normalized = clean_text(text).upper()
    if normalized in {"-", "–", "—", "해당없음", "없음", "N/A"}:
        return False
    if normalized in {"Y", "YES", "TRUE", "필요", "해당"} or "필요" in normalized:
        return True
    if normalized in {"N", "NO", "FALSE", "불필요", "미해당", "없음"} or "불필요" in normalized:
        return False
    return True


def normalize_optional_text(text: str | None) -> str | None:
    cleaned = clean_text(text)
    return cleaned or None


def parse_number(text: str | None) -> float | None:
    if not text:
        return None
    match = re.search(r"\d+(?:\.\d+)?", text.replace(",", ""))
    if not match:
        return None
    return float(match.group(0))


def parse_int(text: str | None) -> int | None:
    if not text:
        return None
    digits = re.sub(r"\D", "", text)
    if not digits:
        return None
    return int(digits)


def extract_notice_body_text(soup: BeautifulSoup) -> str | None:
    selectors = [
        ".board-view",
        ".bbs-view",
        ".post-view",
        ".view-wrap",
        ".view",
        ".detail-content",
        ".view-content",
        ".board-view-content",
        ".bbs-view-content",
        ".content-area",
        "article",
        ".content",
        "#content",
    ]

    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            for tag in element.find_all(["script", "style", "nav", "header", "footer"]):
                tag.decompose()
            text = clean_text(element.get_text(" ", strip=True))
            text = trim_notice_noise(text)
            if text and len(text) >= 20:
                return text

    body = soup.find("body")
    if body:
        for tag in body.find_all(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        text = clean_text(body.get_text(" ", strip=True))
        return trim_notice_noise(text) or None

    text = clean_text(soup.get_text(" ", strip=True))
    return trim_notice_noise(text) or None


def extract_title(soup: BeautifulSoup) -> str | None:
    selectors = ["h1.title", ".view-title", ".board-view-title", ".bbs-view-title", "h1", "h2"]
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            text = clean_text(element.get_text(" ", strip=True))
            if text:
                return text

    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return clean_text(og_title["content"])

    title_tag = soup.find("title")
    if title_tag:
        raw = clean_text(title_tag.get_text(" ", strip=True))
        return re.split(r"\s*[|>-]\s*", raw)[0] or None

    return None


def extract_notice_meta(soup: BeautifulSoup) -> dict[str, str]:
    meta: dict[str, str] = {}

    for row in soup.find_all("tr"):
        cells = [clean_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
        for idx, key in enumerate(cells[:-1]):
            value = cells[idx + 1]
            if key in {"작성자", "담당부서", "부서", "작성부서"} and value:
                meta.setdefault("author", value)
            if key in {"캠퍼스", "구분"} and value:
                meta.setdefault("campus_text", value)

    text = clean_text(soup.get_text(" ", strip=True))
    author = re.search(r"작성자\s*[:：]?\s*([^\s]+)", text)
    if author:
        meta.setdefault("author", author.group(1))

    return meta


def trim_notice_noise(text: str | None) -> str | None:
    """Trim common Kangwon layout text around the actual notice body."""

    if not text:
        return None

    start_markers = ["장학공지 상세", "내용"]
    for marker in start_markers:
        idx = text.find(marker)
        if idx >= 0:
            text = text[idx + len(marker) :].strip()
            break

    end_markers = ["목록으로", "열람하신 페이지", "등록하기 수정 삭제"]
    for marker in end_markers:
        idx = text.find(marker)
        if idx >= 0:
            text = text[:idx].strip()

    return clean_text(text) or None


def extract_attachments(soup: BeautifulSoup, detail_url: str) -> dict[str, list[str]]:
    files: list[str] = []
    images: list[str] = []

    for link in soup.find_all("a", href=True):
        absolute = urljoin(detail_url, link["href"])
        ext = infer_attachment_ext(absolute, link.get_text(" ", strip=True))
        if ext in {"pdf", "hwp", "hwpx", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "zip"}:
            if not absolute.lower().startswith(("javascript:", "#")):
                files.append(absolute)

    for image in soup.find_all("img", src=True):
        absolute = urljoin(detail_url, image["src"])
        images.append(absolute)

    return {"files": unique(files), "images": unique(images)}


def infer_attachment_ext(url: str, link_text: str | None = None) -> str:
    """Infer file type from path, download query params, or visible filename."""

    parts = urlsplit(url)
    candidates = [
        PurePosixPath(parts.path).suffix.lower().lstrip("."),
    ]
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    for key in ("fn", "dn", "fileName", "filename"):
        value = query.get(key)
        if value:
            candidates.append(PurePosixPath(unquote(value)).suffix.lower().lstrip("."))
    if link_text:
        match = re.search(r"\.([A-Za-z0-9]{2,5})(?:\b|$)", clean_text(link_text))
        if match:
            candidates.append(match.group(1).lower())

    allowed = {"pdf", "hwp", "hwpx", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "zip"}
    for candidate in candidates:
        if candidate in allowed:
            return candidate
    return ""


def extract_phone(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"(?:문의|전화|연락처)?\s*(0\d{1,2}-\d{3,4}-\d{4})", text)
    return match.group(1) if match else None


def find_campus(values: list[str]) -> str | None:
    for value in values:
        if any(keyword in value for keyword in ("춘천", "삼척", "도계")):
            return value
    return None


def find_date_text(values: list[str]) -> str | None:
    for value in values:
        if re.search(r"\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}", value):
            return value
    return None


def find_view_count(values: list[str]) -> int | None:
    for value in reversed(values):
        digits = re.sub(r"\D", "", value)
        if digits and len(digits) <= 8:
            try:
                return int(digits)
            except ValueError:
                return None
    return None


def find_author(
    values: list[str],
    title: str,
    campus: str | None,
    created_at: str | None,
    views: int | None,
) -> str | None:
    ignored = {title}
    if campus:
        ignored.add(campus)
    if created_at:
        ignored.add(created_at)
    if views is not None:
        ignored.add(str(views))

    for value in values:
        if not value or value in ignored:
            continue
        if re.search(r"\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}", value):
            continue
        if value.isdigit():
            continue
        if len(value) <= 30:
            return value
    return None


def pick(fields: dict[str, str], *labels: str) -> str | None:
    for label in labels:
        if label in fields and fields[label]:
            return fields[label]
    return None


def first_value(values: list[str]) -> str | None:
    return values[0] if values else None


def first_attachment_type(values: list[str]) -> str | None:
    if not values:
        return None
    ext = PurePosixPath(urlsplit(values[0]).path).suffix.lower().lstrip(".")
    return ext.upper() if ext else None


def attachment_types(values: list[str]) -> list[str]:
    types = []
    for value in values:
        ext = infer_attachment_ext(value)
        if ext:
            types.append(ext.upper())
    return unique(types)


def unique(values: list[str]) -> list[str]:
    seen = set()
    results = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        results.append(value)
    return results


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    icon_noise = [
        "chevron_forward",
        "keyboard_arrow_down",
        "arrow_left_alt",
        "check_circle",
        "radio_button_unchecked",
        "radio_button_checked",
    ]
    for token in icon_noise:
        text = text.replace(token, " ")
    return re.sub(r"\s+", " ", text).strip()


def format_date(year: str, month: str, day: str) -> str | None:
    try:
        return date(int(year), int(month), int(day)).isoformat()
    except ValueError:
        return None


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
