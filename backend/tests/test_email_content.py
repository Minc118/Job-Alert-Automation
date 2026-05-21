from __future__ import annotations

import base64

from job_alert_automation.email_content import (
    body_hash,
    extract_bodies_from_gmail_message,
    html_to_text,
    preferred_text_body,
)


def _gmail_data(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")


def test_extract_bodies_from_nested_gmail_message() -> None:
    message = {
        "payload": {
            "mimeType": "multipart/alternative",
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": _gmail_data("Werkstudent AI\nBerlin")},
                },
                {
                    "mimeType": "text/html",
                    "body": {"data": _gmail_data("<html><body><p>Werkstudent AI</p><p>Berlin</p></body></html>")},
                },
            ],
        }
    }

    text_body, html_body = extract_bodies_from_gmail_message(message)

    assert text_body == "Werkstudent AI\nBerlin"
    assert html_body == "<html><body><p>Werkstudent AI</p><p>Berlin</p></body></html>"


def test_preferred_text_body_falls_back_to_html_text() -> None:
    body = preferred_text_body(None, "<html><body><p>Junior Project Manager</p><p>Berlin</p></body></html>")

    assert body == "Junior Project Manager\nBerlin"


def test_html_to_text_normalizes_whitespace() -> None:
    assert html_to_text("<div>One</div><br><div>Two</div>") == "One\nTwo"


def test_body_hash_is_stable_and_ignores_empty_bodies() -> None:
    assert body_hash("hello") == body_hash("hello")
    assert body_hash(None, "") is None
