from __future__ import annotations

import base64
import hashlib
import re
from html.parser import HTMLParser
from typing import Any


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self._chunks.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"br", "p", "div", "li", "tr"}:
            self._chunks.append("\n")

    def text(self) -> str:
        return normalize_body_text(" ".join(self._chunks))


def decode_gmail_body_data(data: str | None) -> str:
    if not data:
        return ""
    padded = data + "=" * (-len(data) % 4)
    decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
    return decoded.decode("utf-8", errors="replace")


def normalize_body_text(value: str | None) -> str:
    if not value:
        return ""
    text = value.replace("\u00a0", " ")
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n\s+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def html_to_text(html: str | None) -> str:
    if not html:
        return ""
    extractor = _HTMLTextExtractor()
    extractor.feed(html)
    return extractor.text()


def _walk_parts(part: dict[str, Any]) -> list[dict[str, Any]]:
    parts = [part]
    for child in part.get("parts") or []:
        parts.extend(_walk_parts(child))
    return parts


def extract_bodies_from_gmail_message(message: dict[str, Any]) -> tuple[str | None, str | None]:
    payload = message.get("payload") or {}
    text_chunks: list[str] = []
    html_chunks: list[str] = []

    for part in _walk_parts(payload):
        mime_type = str(part.get("mimeType") or "").lower()
        body = part.get("body") or {}
        content = decode_gmail_body_data(body.get("data"))
        if not content:
            continue
        if mime_type == "text/plain":
            text_chunks.append(content)
        elif mime_type == "text/html":
            html_chunks.append(content)

    text_body = normalize_body_text("\n\n".join(text_chunks))
    html_body = "\n\n".join(chunk.strip() for chunk in html_chunks if chunk.strip()).strip()
    return text_body or None, html_body or None


def body_hash(*bodies: str | None) -> str | None:
    joined = "\n\n".join(normalize_body_text(body) for body in bodies if body)
    if not joined:
        return None
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def preferred_text_body(text_body: str | None, html_body: str | None) -> str | None:
    if text_body:
        return normalize_body_text(text_body)
    converted = html_to_text(html_body)
    return converted or None
