from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.schemas import AuthenticatedUserResponse, MeResponse
from api.services.auth_service import VerifiedIdentity, get_or_create_app_profile, verify_neon_auth_jwt


router = APIRouter(prefix="/api", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def verify_current_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> VerifiedIdentity:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return verify_neon_auth_jwt(credentials.credentials)


def optional_current_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> VerifiedIdentity | None:
    if credentials is None:
        return None
    if credentials.scheme.lower() != "bearer" or not credentials.credentials.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return verify_neon_auth_jwt(credentials.credentials)


def resolve_request_user_id(user_id: str | None, identity: VerifiedIdentity | None) -> tuple[str, bool]:
    if identity is not None:
        return get_or_create_app_profile(identity).user.id, True
    if user_id:
        return user_id, False
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")


@router.get("/me", response_model=MeResponse)
def get_me(identity: VerifiedIdentity = Depends(verify_current_identity)) -> MeResponse:
    app_profile = get_or_create_app_profile(identity)
    return MeResponse(
        authenticated=True,
        authProvider="neon",
        user=AuthenticatedUserResponse(
            subject=identity.subject,
            displayName=identity.display_name,
            email=identity.email,
        ),
        appUser=app_profile.user,
        accountDataReady=True,
        onboardingComplete=app_profile.onboarding_complete,
    )
