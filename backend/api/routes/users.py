from __future__ import annotations

from fastapi import APIRouter, Depends

from api.routes.me import verify_current_identity
from api.schemas import OnboardingCompleteResponse, UserPreferencesResponse, UserPreferencesUpdate, UserResponse
from api.services.auth_service import VerifiedIdentity, complete_onboarding, get_or_create_app_profile
from api.services.preference_service import get_preferences, update_preferences
from api.services.user_service import list_users


router = APIRouter(prefix="/api", tags=["users"])


@router.get("/users", response_model=list[UserResponse])
def get_users() -> list[UserResponse]:
    return list_users()


@router.get("/user/preferences", response_model=UserPreferencesResponse)
def get_current_user_preferences(identity: VerifiedIdentity = Depends(verify_current_identity)) -> UserPreferencesResponse:
    profile = get_or_create_app_profile(identity)
    return get_preferences(profile.user.id)


@router.patch("/user/preferences", response_model=UserPreferencesResponse)
def update_current_user_preferences(
    payload: UserPreferencesUpdate,
    identity: VerifiedIdentity = Depends(verify_current_identity),
) -> UserPreferencesResponse:
    profile = get_or_create_app_profile(identity)
    return update_preferences(profile.user.id, payload)


@router.post("/onboarding/complete", response_model=OnboardingCompleteResponse)
def finish_current_user_onboarding(identity: VerifiedIdentity = Depends(verify_current_identity)) -> OnboardingCompleteResponse:
    profile = complete_onboarding(identity)
    return OnboardingCompleteResponse(userId=profile.user.id, onboardingComplete=profile.onboarding_complete)
