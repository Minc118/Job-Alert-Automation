from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status

from api.schemas import UserDocumentDeleteResponse, UserDocumentPreviewResponse, UserDocumentResponse
from api.services.database import readonly_connection, write_connection
from job_alert_automation.config import REPO_ROOT


PRIVATE_UPLOADS_DIR = REPO_ROOT / "private" / "uploads"
DOCUMENT_TYPES = {"profile_markdown", "resume_pdf", "cover_letter_template"}
TEXT_DOCUMENT_TYPES = {"profile_markdown", "cover_letter_template"}
MAX_TEXT_FILE_BYTES = 256 * 1024
MAX_RESUME_FILE_BYTES = 5 * 1024 * 1024
PREVIEW_CHARS = 6000
SAFE_DOCUMENT_NOT_FOUND = "Document was not found for this account."


def _datetime_to_string(value: Any) -> str:
    return value.isoformat(sep=" ", timespec="seconds") if value is not None else ""


def _document_from_row(row: Any) -> UserDocumentResponse:
    return UserDocumentResponse(
        id=int(row[0]),
        userId=str(row[1]),
        documentType=str(row[2]),  # type: ignore[arg-type]
        originalFilename=str(row[3]),
        mimeType=row[4],
        fileSizeBytes=int(row[5]) if row[5] is not None else None,
        isActive=bool(row[6]),
        createdAt=_datetime_to_string(row[7]),
    )


def _clean_filename(filename: str | None) -> str:
    raw = Path(filename or "document").name.strip()
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("._")
    return cleaned[:120] or "document"


def _validate_document_type(document_type: str) -> str:
    if document_type not in DOCUMENT_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unsupported document type.")
    return document_type


def _safe_stored_path(stored_path: str) -> Path:
    candidate = (REPO_ROOT / stored_path).resolve()
    if not candidate.is_relative_to(PRIVATE_UPLOADS_DIR.resolve()):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Private document storage is invalid.")
    return candidate


def _validate_upload(document_type: str, upload: UploadFile, data: bytes) -> tuple[str, str]:
    filename = _clean_filename(upload.filename)
    suffix = Path(filename).suffix.casefold()
    content_type = (upload.content_type or "application/octet-stream").casefold()

    if document_type in TEXT_DOCUMENT_TYPES:
        if suffix not in {".md", ".markdown"}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Profile and template documents must be Markdown files.")
        if len(data) > MAX_TEXT_FILE_BYTES:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Markdown document is too large.")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Markdown document must be UTF-8 text.") from exc
        return filename, content_type if content_type in {"text/markdown", "text/plain"} else "text/markdown"

    if suffix != ".pdf":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Resume document must be a PDF file.")
    if len(data) > MAX_RESUME_FILE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Resume PDF is too large.")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Resume document must be a PDF file.")
    return filename, "application/pdf"


def list_documents(user_id: str) -> list[UserDocumentResponse]:
    with readonly_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, document_type, original_filename, mime_type, file_size_bytes, is_active, created_at
            FROM user_documents
            WHERE user_id = %s
            ORDER BY is_active DESC, created_at DESC, id DESC
            """,
            (user_id,),
        ).fetchall()
    return [_document_from_row(row) for row in rows]


def _owned_document_row(user_id: str, document_id: int) -> Any:
    with readonly_connection() as conn:
        row = conn.execute(
            """
            SELECT id, user_id, document_type, original_filename, mime_type, file_size_bytes, is_active, created_at, stored_path
            FROM user_documents
            WHERE user_id = %s AND id = %s
            """,
            (user_id, document_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=SAFE_DOCUMENT_NOT_FOUND)
    return row


async def store_document_upload(user_id: str, *, document_type: str, upload: UploadFile) -> UserDocumentResponse:
    document_type = _validate_document_type(document_type)
    data = await upload.read(MAX_RESUME_FILE_BYTES + 1)
    filename, mime_type = _validate_upload(document_type, upload, data)

    user_dir = PRIVATE_UPLOADS_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    stored_path = user_dir / f"{uuid.uuid4().hex}_{filename}"
    stored_path.write_bytes(data)
    stored_path_value = str(stored_path.relative_to(REPO_ROOT))

    try:
        with write_connection() as conn:
            conn.execute(
                """
                UPDATE user_documents
                SET is_active = false
                WHERE user_id = %s AND document_type = %s AND is_active IS TRUE
                """,
                (user_id, document_type),
            )
            row = conn.execute(
                """
                INSERT INTO user_documents (
                    user_id, document_type, original_filename, stored_path, mime_type, file_size_bytes, is_active
                )
                VALUES (%s, %s, %s, %s, %s, %s, true)
                RETURNING id, user_id, document_type, original_filename, mime_type, file_size_bytes, is_active, created_at
                """,
                (user_id, document_type, filename, stored_path_value, mime_type, len(data)),
            ).fetchone()
            conn.commit()
    except Exception:
        stored_path.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()

    return _document_from_row(row)


def activate_document(user_id: str, document_id: int) -> UserDocumentResponse:
    owned = _owned_document_row(user_id, document_id)
    document_type = str(owned[2])
    with write_connection() as conn:
        conn.execute(
            """
            UPDATE user_documents
            SET is_active = false
            WHERE user_id = %s AND document_type = %s
            """,
            (user_id, document_type),
        )
        row = conn.execute(
            """
            UPDATE user_documents
            SET is_active = true
            WHERE user_id = %s AND id = %s
            RETURNING id, user_id, document_type, original_filename, mime_type, file_size_bytes, is_active, created_at
            """,
            (user_id, document_id),
        ).fetchone()
        conn.commit()
    return _document_from_row(row)


def delete_document(user_id: str, document_id: int) -> UserDocumentDeleteResponse:
    owned = _owned_document_row(user_id, document_id)
    stored_path = _safe_stored_path(str(owned[8]))
    with write_connection() as conn:
        conn.execute("DELETE FROM user_documents WHERE user_id = %s AND id = %s", (user_id, document_id))
        conn.commit()
    stored_path.unlink(missing_ok=True)
    return UserDocumentDeleteResponse(documentId=document_id, deleted=True)


def preview_document(user_id: str, document_id: int) -> UserDocumentPreviewResponse:
    owned = _owned_document_row(user_id, document_id)
    document_type = str(owned[2])
    if document_type not in TEXT_DOCUMENT_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Preview is available for Markdown documents only.")
    content = _safe_stored_path(str(owned[8])).read_text(encoding="utf-8")
    return UserDocumentPreviewResponse(
        documentId=document_id,
        documentType=document_type,  # type: ignore[arg-type]
        content=content[:PREVIEW_CHARS],
        truncated=len(content) > PREVIEW_CHARS,
    )


def load_active_profile_summary(user_id: str) -> str | None:
    with readonly_connection() as conn:
        row = conn.execute(
            """
            SELECT stored_path
            FROM user_documents
            WHERE user_id = %s
              AND document_type = 'profile_markdown'
              AND is_active IS TRUE
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
    if row is None:
        return None
    content = _safe_stored_path(str(row[0])).read_text(encoding="utf-8")
    return content[:PREVIEW_CHARS]
