from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from api.routes.me import verify_current_identity
from api.schemas import GmailConnectionStatusResponse, GmailConnectResponse, GmailFetchResponse
from api.services.auth_service import VerifiedIdentity, get_or_create_app_profile
from api.services.gmail_fetch_service import run_connected_gmail_fetch
from api.services.gmail_oauth_service import (
    SAFE_GMAIL_CALLBACK_ERROR,
    complete_callback,
    create_authorization_url,
    disconnect_gmail,
    get_connection_status,
)


router = APIRouter(prefix="/api/gmail", tags=["gmail"])


@router.get("/status", response_model=GmailConnectionStatusResponse)
def gmail_status(identity: VerifiedIdentity = Depends(verify_current_identity)) -> GmailConnectionStatusResponse:
    profile = get_or_create_app_profile(identity)
    return get_connection_status(profile.user.id)


@router.post("/connect", response_model=GmailConnectResponse)
def gmail_connect(identity: VerifiedIdentity = Depends(verify_current_identity)) -> GmailConnectResponse:
    profile = get_or_create_app_profile(identity)
    return GmailConnectResponse(authorizationUrl=create_authorization_url(profile.user.id))


@router.get("/callback")
def gmail_callback(
    state: str = Query(...),
    code: str | None = Query(None),
    error: str | None = Query(None),
) -> RedirectResponse:
    if error or not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SAFE_GMAIL_CALLBACK_ERROR)
    return RedirectResponse(complete_callback(state_value=state, code=code), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/disconnect", response_model=GmailConnectionStatusResponse)
def gmail_disconnect(identity: VerifiedIdentity = Depends(verify_current_identity)) -> GmailConnectionStatusResponse:
    profile = get_or_create_app_profile(identity)
    return disconnect_gmail(profile.user.id)


@router.post("/fetch", response_model=GmailFetchResponse)
def gmail_fetch(
    max_results_per_source: int = Query(10, ge=1, le=50),
    identity: VerifiedIdentity = Depends(verify_current_identity),
) -> GmailFetchResponse:
    profile = get_or_create_app_profile(identity)
    return run_connected_gmail_fetch(profile.user.id, max_results_per_source=max_results_per_source)
