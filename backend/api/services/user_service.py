from __future__ import annotations

from fastapi import HTTPException, status

from api.schemas import UserResponse
from job_alert_automation.config import ConfigError, load_users_config


def list_users() -> list[UserResponse]:
    try:
        config = load_users_config()
    except ConfigError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User configuration could not be loaded.") from exc
    return [UserResponse(id=user.id, displayName=user.display_name) for user in config.users.values()]


def validate_user_id(user_id: str) -> None:
    try:
        config = load_users_config()
        config.validate_user_id(user_id)
    except ConfigError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown or invalid user.") from exc
