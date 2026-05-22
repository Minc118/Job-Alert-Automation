from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from api.routes.me import verify_current_identity
from api.schemas import UserDocumentDeleteResponse, UserDocumentPreviewResponse, UserDocumentResponse
from api.services.auth_service import VerifiedIdentity, get_or_create_app_profile
from api.services.document_service import activate_document, delete_document, list_documents, preview_document, store_document_upload


router = APIRouter(prefix="/api", tags=["documents"])


def _current_app_user_id(identity: VerifiedIdentity) -> str:
    return get_or_create_app_profile(identity).user.id


@router.get("/user/documents", response_model=list[UserDocumentResponse])
def get_current_user_documents(identity: VerifiedIdentity = Depends(verify_current_identity)) -> list[UserDocumentResponse]:
    return list_documents(_current_app_user_id(identity))


@router.post("/user/documents", response_model=UserDocumentResponse)
async def upload_current_user_document(
    document_type: Annotated[str, Form(alias="documentType")],
    file: Annotated[UploadFile, File()],
    identity: VerifiedIdentity = Depends(verify_current_identity),
) -> UserDocumentResponse:
    return await store_document_upload(_current_app_user_id(identity), document_type=document_type, upload=file)


@router.patch("/user/documents/{document_id}/activate", response_model=UserDocumentResponse)
def activate_current_user_document(
    document_id: int,
    identity: VerifiedIdentity = Depends(verify_current_identity),
) -> UserDocumentResponse:
    return activate_document(_current_app_user_id(identity), document_id)


@router.delete("/user/documents/{document_id}", response_model=UserDocumentDeleteResponse)
def delete_current_user_document(
    document_id: int,
    identity: VerifiedIdentity = Depends(verify_current_identity),
) -> UserDocumentDeleteResponse:
    return delete_document(_current_app_user_id(identity), document_id)


@router.get("/user/documents/{document_id}/preview", response_model=UserDocumentPreviewResponse)
def preview_current_user_document(
    document_id: int,
    identity: VerifiedIdentity = Depends(verify_current_identity),
) -> UserDocumentPreviewResponse:
    return preview_document(_current_app_user_id(identity), document_id)
