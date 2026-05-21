from __future__ import annotations

import pytest

from job_alert_automation.config import ConfigError, get_database_url, load_users_config


def test_users_yaml_loads_expected_users() -> None:
    config = load_users_config()

    assert set(config.users) == {"minjian", "chang"}
    assert config.users["minjian"].display_name == "Minjian"
    assert config.users["chang"].display_name == "Chang"


def test_user_preferences_are_present() -> None:
    config = load_users_config()

    for user_id in ("minjian", "chang"):
        preferences = config.preferences[user_id]
        assert preferences.target_role_keywords
        assert preferences.preferred_locations
        assert "linkedin" in preferences.source_queries
        assert "stepstone" in preferences.source_queries
        assert "indeed" in preferences.source_queries


def test_config_loading_does_not_require_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    config = load_users_config()

    assert "minjian" in config.users


def test_missing_database_url_error_is_safe(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ConfigError) as exc_info:
        get_database_url(required=True, env_path=tmp_path / "missing.env")

    message = str(exc_info.value)
    assert "DATABASE_URL is required" in message
    assert "postgres://" not in message
    assert "postgresql://" not in message
