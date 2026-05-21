from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import yaml

from .models import AppUser, UserPreferences


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
DEFAULT_USERS_CONFIG_PATH = BACKEND_ROOT / "config" / "users.yaml"
DEFAULT_ENV_PATH = REPO_ROOT / ".env"


class ConfigError(RuntimeError):
    """Raised for safe, user-facing configuration errors."""


@dataclass(frozen=True)
class LoadedConfig:
    users: dict[str, AppUser]
    preferences: dict[str, UserPreferences]

    def validate_user_id(self, user_id: str | None) -> list[str]:
        if user_id is None:
            return list(self.users.keys())
        if user_id not in self.users:
            available = ", ".join(sorted(self.users))
            raise ConfigError(f"Unknown user '{user_id}'. Available users: {available}.")
        return [user_id]


def _as_string_list(value: Any, field_name: str, user_id: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"User '{user_id}' field '{field_name}' must be a list of strings.")
    return tuple(item for item in value if item.strip())


def _as_source_queries(value: Any, user_id: str) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"User '{user_id}' field 'source_queries' must be a mapping.")
    result: dict[str, str] = {}
    for source, query in value.items():
        if not isinstance(source, str) or not isinstance(query, str):
            raise ConfigError(f"User '{user_id}' source queries must map strings to strings.")
        result[source] = query
    return result


def load_users_config(path: Path | None = None) -> LoadedConfig:
    config_path = path or DEFAULT_USERS_CONFIG_PATH
    if not config_path.exists():
        raise ConfigError(f"User config not found at {config_path}.")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    users_raw = raw.get("users")
    if not isinstance(users_raw, dict) or not users_raw:
        raise ConfigError("User config must contain a non-empty 'users' mapping.")

    users: dict[str, AppUser] = {}
    preferences: dict[str, UserPreferences] = {}

    for user_id, user_raw in users_raw.items():
        if not isinstance(user_id, str) or not isinstance(user_raw, dict):
            raise ConfigError("Each configured user must be a mapping keyed by user id.")
        display_name = user_raw.get("display_name")
        if not isinstance(display_name, str) or not display_name.strip():
            raise ConfigError(f"User '{user_id}' must define a display_name.")

        email = user_raw.get("email")
        if email is not None and not isinstance(email, str):
            raise ConfigError(f"User '{user_id}' email must be a string when set.")

        users[user_id] = AppUser(id=user_id, display_name=display_name, email=email)
        preferences[user_id] = UserPreferences(
            user_id=user_id,
            target_role_keywords=_as_string_list(
                user_raw.get("target_role_keywords"), "target_role_keywords", user_id
            ),
            preferred_locations=_as_string_list(
                user_raw.get("preferred_locations"), "preferred_locations", user_id
            ),
            excluded_keywords=_as_string_list(
                user_raw.get("excluded_keywords"), "excluded_keywords", user_id
            ),
            source_queries=_as_source_queries(user_raw.get("source_queries"), user_id),
        )

    return LoadedConfig(users=users, preferences=preferences)


def get_database_url(*, required: bool = False, env_path: Path | None = None) -> str | None:
    dotenv_path = env_path or DEFAULT_ENV_PATH
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path, override=False)

    value = os.getenv("DATABASE_URL")
    if value is not None:
        value = value.strip()

    if required and not value:
        raise ConfigError("DATABASE_URL is required for this command. Add it to your local .env file.")
    return value or None


def get_env_value(name: str, *, default: str | None = None, env_path: Path | None = None) -> str:
    dotenv_path = env_path or DEFAULT_ENV_PATH
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path, override=False)

    value = os.getenv(name)
    if value is None or not value.strip():
        if default is None:
            raise ConfigError(f"{name} is required in your local .env file.")
        return default
    return value.strip()
