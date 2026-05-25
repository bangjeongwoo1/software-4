"""Gemini client and source attachment loading."""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from urllib.parse import parse_qsl, unquote, urlparse

import requests

from . import llm_config as config
from .llm_parser import parse_response


@dataclass(frozen=True)
class DownloadedAsset:
    url: str
    data: bytes
    mime_type: str


def call_gemini(
    *,
    raw_text: str | None,
    image_url: str | None = None,
    pdf_url: str | None = None,
    prompt_type: str = "notice",
) -> dict:
    """Send text/assets to Gemini and return a validated parsed payload."""

    config.validate_gemini_config()

    from google import genai
    from google.genai import types

    contents: list[object] = []
    if raw_text:
        contents.append(build_text_prompt(raw_text, prompt_type=prompt_type))

    if prompt_type == "notice":
        for asset in collect_assets(image_url=image_url, pdf_url=pdf_url):
            contents.append(types.Part.from_bytes(data=asset.data, mime_type=asset.mime_type))

    if not contents:
        raise ValueError("No text, image, or PDF content available for Gemini")

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=config.SYSTEM_PROMPTS[prompt_type],
            response_mime_type="application/json",
            temperature=0,
        ),
    )
    return parse_response(response.text or "", target=prompt_type)


def build_text_prompt(raw_text: str, *, prompt_type: str = "notice") -> str:
    if prompt_type == "contest":
        return raw_text
    return (
        "Analyze this Kangwon National University scholarship notice text. "
        "Use attached image/PDF evidence too if provided.\n\n"
        f"{raw_text}"
    )


def collect_assets(*, image_url: str | None, pdf_url: str | None) -> list[DownloadedAsset]:
    assets: list[DownloadedAsset] = []

    for url in split_urls(image_url):
        asset = download_asset(url)
        if asset and asset.mime_type.startswith("image/"):
            assets.append(asset)

    for url in split_urls(pdf_url):
        if not looks_like_pdf(url):
            continue
        asset = download_asset(url)
        if asset and (asset.mime_type == "application/pdf" or looks_like_pdf(url)):
            assets.append(DownloadedAsset(asset.url, asset.data, "application/pdf"))

    return assets


def split_urls(value: str | None) -> list[str]:
    if not value:
        return []
    urls = []
    for part in str(value).replace("\r", "\n").split("\n"):
        part = part.strip()
        if part:
            urls.append(part)
    return urls


def download_asset(url: str) -> DownloadedAsset | None:
    try:
        response = requests.get(
            url,
            timeout=config.REQUEST_TIMEOUT,
            headers={"User-Agent": config.USER_AGENT},
        )
        response.raise_for_status()
    except requests.RequestException:
        return None

    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    guessed_type = sniff_mime_type(response.content) or guess_mime_type(url)
    mime_type = guessed_type if is_generic_mime_type(content_type) else content_type or guessed_type
    if not mime_type:
        return None
    return DownloadedAsset(url=url, data=response.content, mime_type=mime_type)


def guess_mime_type(url: str) -> str | None:
    parsed = urlparse(url)
    candidates = [parsed.path]
    candidates.extend(value for _, value in parse_qsl(parsed.query, keep_blank_values=True))
    for candidate in candidates:
        guessed, _ = mimetypes.guess_type(unquote(candidate))
        if guessed:
            return guessed
    return None


def sniff_mime_type(data: bytes) -> str | None:
    if data.startswith(b"%PDF"):
        return "application/pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "image/gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def is_generic_mime_type(mime_type: str | None) -> bool:
    return not mime_type or mime_type in {"application/octet-stream", "binary/octet-stream"}


def looks_like_pdf(url: str) -> bool:
    return ".pdf" in unquote(urlparse(url).path + "?" + urlparse(url).query).lower()
