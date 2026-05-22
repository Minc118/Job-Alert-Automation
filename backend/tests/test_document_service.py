from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from api.services import document_service


def test_validate_profile_upload_requires_markdown() -> None:
    upload = SimpleNamespace(filename="profile.txt", content_type="text/plain")

    with pytest.raises(HTTPException) as exc_info:
        document_service._validate_upload("profile_markdown", upload, b"Profile text")

    assert exc_info.value.status_code == 422


def test_validate_resume_upload_requires_pdf_signature() -> None:
    upload = SimpleNamespace(filename="resume.pdf", content_type="application/pdf")

    with pytest.raises(HTTPException) as exc_info:
        document_service._validate_upload("resume_pdf", upload, b"not a pdf")

    assert exc_info.value.status_code == 422


def test_validate_profile_upload_accepts_utf8_markdown() -> None:
    upload = SimpleNamespace(filename="profile.md", content_type="text/markdown")

    filename, mime_type = document_service._validate_upload("profile_markdown", upload, b"# Profile")

    assert filename == "profile.md"
    assert mime_type == "text/markdown"
