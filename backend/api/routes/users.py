from __future__ import annotations

from fastapi import APIRouter

from api.schemas import UserResponse
from api.services.user_service import list_users


router = APIRouter(prefix="/api", tags=["users"])


@router.get("/users", response_model=list[UserResponse])
def get_users() -> list[UserResponse]:
    return list_users()
