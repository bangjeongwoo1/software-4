"""HTML parsers for the ContestKorea crawler."""

from __future__ import annotations

import re
from datetime import date
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

try:
    from . import contest_config as config
except ImportError:  # pragma: no cover
    import contest_config as config  # type: ignore


def parse_contest_list(html: str, page_url: str, *, year: int | None = None) -> list[dict]:
    """Parse ContestKorea list cards into DB-ready list-level rows."""

    soup = BeautifulSoup(html, "html.parser")
    current_year = year or date.today().year
    items: list[dict] = []

    for card in find_list_cards(soup):
        link = find_card_detail_link(card)
        if not link:
            continue

        href = link["href"]
        str_no = extract_str_no(href)
        if not str_no:
            continue

        detail_url = normalize_detail_url(href, page_url)
        text = clean_text(card.get_text(" ", strip=True) if card else link.get_text(" ", strip=True))
        status = extract_status(text)
        if status not in config.VALID_STATUSES:
            continue

        title = extract_card_title(card, link) or extract_title_from_text(text)
        if not title:
            continue

        reception_start, reception_end = parse_labeled_date_range(text, "접수", current_year)
        review_start, review_end = parse_labeled_date_range(text, "심사", current_year)
        announcement_date = parse_labeled_single_date(text, "발표", current_year)

        items.append(
            {
                "str_no": str_no,
                "title": title,
                "host": extract_card_host(card) or extract_labeled_value(text, "주최"),
                "target_text": extract_card_target(card) or extract_labeled_value(text, "대상"),
                "reception_start": reception_start,
                "reception_end": reception_end,
                "review_start": review_start,
                "review_end": review_end,
                "announcement_date": announcement_date,
                "d_day": extract_d_day(text) or calc_d_day(reception_end),
                "status": status,
                "status_text": extract_status_text(text),
                "detail_url": detail_url,
            }
        )

    return unique_by_detail_url(items)


def parse_contest_detail(html: str, detail_url: str, list_item: dict | None = None) -> dict:
    """Parse ContestKorea detail table and raw detail text."""

    soup = BeautifulSoup(html, "html.parser")
    detail = parse_detail_table(soup, detail_url)
    detail.setdefault("detail_text", parse_detail_text(soup))
    normalize_contest_urls(detail)

    if list_item:
        detail.setdefault("host_organization", list_item.get("host"))
        detail.setdefault("target_text", list_item.get("target_text"))

    return detail


def parse_detail_table(soup: BeautifulSoup, detail_url: str) -> dict:
    """Parse the two-column detail information table."""

    result: dict[str, str | None] = {}
    label_map = {
        "주최": "host_organization",
        "주관": "host_organization",
        "대표분야": "main_field",
        "참가대상": "target_text",
        "접수기간": "reception_period_text",
        "심사기간": "review_period_text",
        "대회지역": "contest_region",
        "시상내역": "award_text",
        "접수방법": "application_method",
        "참가비용": "participation_fee",
    }

    for row in soup.select("table tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) < 2:
            continue

        label = clean_text(cells[0].get_text(" ", strip=True))
        value_cell = cells[1]
        value = clean_text(value_cell.get_text(" ", strip=True)) or None
        if not label:
            continue

        if "접수하기" in label:
            result["application_url"] = extract_first_link(value_cell, detail_url) or value
            continue
        if "홈페이지" in label:
            result["homepage_url"] = extract_first_link(value_cell, detail_url) or value
            continue

        for keyword, column in label_map.items():
            if keyword in label:
                if column == "host_organization" and result.get(column) and value:
                    result[column] = f"{result[column]} / {value}"
                else:
                    result[column] = value
                break

    return result


def parse_detail_text(soup: BeautifulSoup) -> str | None:
    """Extract raw detail text from the main content area."""

    guideline = soup.select_one(".view_detail_area > .txt, .view_detail_area .txt")
    if guideline:
        text = extract_guideline_text(guideline)
        if text:
            return text

    selectors = [
        ".view-content",
        ".board-view-content",
        ".bbs-view-content",
        ".view_cont",
        ".viewCon",
        ".content",
        "article",
    ]
    for selector in selectors:
        section = soup.select_one(selector)
        if section:
            text = clean_multiline_text(section.get_text("\n", strip=True))
            if text:
                return text

    body = soup.find("body")
    if body:
        for tag in body.find_all(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        return clean_multiline_text(body.get_text("\n", strip=True)) or None

    return clean_multiline_text(soup.get_text("\n", strip=True)) or None


def extract_guideline_text(element) -> str:
    """Extract only the contest guideline text, excluding shared page chrome."""

    lines: list[str] = []
    for child in element.find_all(recursive=False):
        classes = set(child.get("class", []))
        if "attachments" in classes or "img_area" in classes:
            continue
        if child.name == "h1" and "line" in classes:
            break
        if child.name in {"script", "style"}:
            continue

        child_copy = BeautifulSoup(str(child), "html.parser")
        for tag in child_copy.select("a#btn_requ, img, script, style"):
            tag.decompose()

        text = clean_multiline_text(child_copy.get_text("\n", strip=True))
        if text:
            lines.append(text)

    return "\n".join(lines).strip()


def normalize_detail_url(href: str, page_url: str | None = None) -> str:
    """Normalize detail URLs to int_gbn and str_no only."""

    absolute = urljoin(page_url or config.BASE_URL, href)
    str_no = extract_str_no(absolute)
    if not str_no:
        return absolute
    return f"{config.BASE_URL}/sub/view.php?int_gbn=1&str_no={str_no}"


def extract_str_no(href: str) -> str | None:
    query = parse_qs(urlparse(href).query)
    value = query.get("str_no", [None])[0]
    return value or None


def find_list_cards(soup: BeautifulSoup) -> list:
    """Return only first-level contest list cards, excluding sidebar/recommendation links."""

    cards = []
    for card in soup.select(".list_style_2 > ul > li"):
        if find_card_detail_link(card) and card.find("ul", class_="host", recursive=False):
            cards.append(card)
    return cards


def find_card_detail_link(card):
    title_box = card.find("div", class_="title", recursive=False)
    if not title_box:
        return None
    for link in title_box.find_all("a", href=True, recursive=False):
        href = link["href"]
        if "view.php" in href and "str_no=" in href:
            return link
    return None


def extract_status(text: str) -> str | None:
    status_text = extract_status_text(text)
    if not status_text:
        return None
    return config.STATUS_MAP.get(status_text)


def extract_status_text(text: str) -> str | None:
    for korean_status in config.STATUS_MAP:
        if korean_status in text:
            return korean_status
    return None


def parse_labeled_date_range(text: str, label: str, year: int) -> tuple[str | None, str | None]:
    match = re.search(
        rf"{re.escape(label)}\s*[:：]?\s*(\d{{1,2}}\.\d{{1,2}}\s*[~\-]\s*\d{{1,2}}\.\d{{1,2}})",
        text,
    )
    if not match:
        return None, None
    return parse_date_range(match.group(1), year)


def parse_date_range(text: str | None, year: int) -> tuple[str | None, str | None]:
    if not text:
        return None, None

    parts = re.split(r"\s*[~\-]\s*", clean_text(text), maxsplit=1)
    if len(parts) != 2:
        return None, None

    start = parse_month_day(parts[0], year)
    end = parse_month_day(parts[1], year)
    if start and end and end < start:
        end = date(year + 1, end.month, end.day)

    return format_date(start), format_date(end)


def parse_labeled_single_date(text: str, label: str, year: int) -> str | None:
    match = re.search(rf"{re.escape(label)}\s*[:：]?\s*(\d{{1,2}}\.\d{{1,2}})", text)
    if not match:
        return None
    return format_date(parse_month_day(match.group(1), year))


def parse_month_day(text: str, year: int) -> date | None:
    match = re.search(r"(\d{1,2})\s*\.\s*(\d{1,2})", text)
    if not match:
        return None
    try:
        return date(year, int(match.group(1)), int(match.group(2)))
    except ValueError:
        return None


def calc_d_day(reception_end: str | None) -> int | None:
    if not reception_end:
        return None
    try:
        return (date.fromisoformat(reception_end) - date.today()).days
    except ValueError:
        return None


def extract_d_day(text: str) -> int | None:
    match = re.search(r"D\s*[- ]\s*(\d+)", text, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    if "D-Day" in text or "D-day" in text:
        return 0
    return None


def extract_labeled_value(text: str, label: str) -> str | None:
    labels = ["주최", "대상", "접수", "심사", "발표"]
    other_labels = [item for item in labels if item != label]
    stop_pattern = "|".join(re.escape(item) for item in other_labels)
    match = re.search(
        rf"{re.escape(label)}\s*(?:[:：]|\.)\s*(.*?)(?=\s+(?:{stop_pattern})\s*(?:[:：]|\.)|\s+D\s*[- ]?\d+|\s+접수예정|\s+접수중|\s+마감임박|$)",
        text,
    )
    if not match:
        return None
    return clean_text(match.group(1)) or None


def extract_card_title(card, link) -> str | None:
    if card:
        title_el = card.select_one(".title a .txt")
        if title_el:
            title = clean_text(title_el.get_text(" ", strip=True))
            if title:
                return title

    for selector in (".txt",):
        title_el = link.select_one(selector)
        if title_el:
            title = clean_text(title_el.get_text(" ", strip=True))
            if title:
                return title

    category_el = link.select_one(".category")
    if category_el:
        category_el.extract()
    return clean_text(link.get_text(" ", strip=True)) or None


def extract_card_host(card) -> str | None:
    if not card:
        return None
    for item in card.select("ul.host li"):
        text = clean_text(item.get_text(" ", strip=True))
        if "주최" in text:
            return clean_label_noise(text, "주최")
    return None


def extract_card_target(card) -> str | None:
    if not card:
        return None
    for item in card.select("ul.host li"):
        text = clean_text(item.get_text(" ", strip=True))
        if "대상" in text:
            return clean_label_noise(text, "대상")
    return None


def clean_label_noise(text: str, label: str) -> str | None:
    text = re.sub(rf"^{re.escape(label)}\s*(?:[:：]|\.)\s*", "", text)
    return clean_text(text.strip(" .")) or None


def extract_title_from_text(text: str) -> str | None:
    for marker in ("주최", "대상", "접수", "심사", "발표"):
        idx = text.find(marker)
        if idx > 0:
            return clean_text(text[:idx])
    return clean_text(text) or None


def extract_first_link(element, base_url: str) -> str | None:
    link = element.find("a", href=True)
    if not link:
        return None
    href = link["href"].strip()
    if not href or href.startswith(("#", "javascript:")):
        return None
    return urljoin(base_url, href)


def normalize_contest_urls(detail: dict) -> None:
    """Prefer URLs explicitly shown in the contest body over generic button links."""

    detail_text = detail.get("detail_text") or ""
    text_urls = extract_urls_from_text(detail_text)
    if not text_urls:
        return

    application_url = detail.get("application_url")
    if should_replace_application_url(application_url):
        detail["application_url"] = text_urls[0]

    homepage_url = detail.get("homepage_url")
    if homepage_url and homepage_url.startswith("http://"):
        matching = find_same_domain_url(homepage_url, text_urls)
        if matching:
            detail["homepage_url"] = matching


def should_replace_application_url(url: str | None) -> bool:
    if not url:
        return True
    lowered = url.lower()
    return lowered.endswith("/join.php") or "join.php?" in lowered


def extract_urls_from_text(text: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)>\]}\"']+", text or "")
    return unique_strings([url.rstrip(".,;") for url in urls])


def find_same_domain_url(url: str, candidates: list[str]) -> str | None:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    for candidate in candidates:
        candidate_host = urlparse(candidate).netloc.lower().removeprefix("www.")
        if host == candidate_host:
            return candidate
    return None


def unique_strings(values: list[str]) -> list[str]:
    seen = set()
    results = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        results.append(value)
    return results


def unique_by_detail_url(items: list[dict]) -> list[dict]:
    seen = set()
    results = []
    for item in items:
        detail_url = item.get("detail_url")
        if not detail_url or detail_url in seen:
            continue
        seen.add(detail_url)
        results.append(item)
    return results


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def clean_multiline_text(text: str | None) -> str:
    if not text:
        return ""
    lines = [clean_text(line) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def format_date(value: date | None) -> str | None:
    return value.isoformat() if value else None
