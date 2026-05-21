from __future__ import annotations

from pathlib import Path

from job_alert_automation.config import REPO_ROOT


def test_readme_uses_chang_for_future_facing_examples() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "chang" in readme
    legacy_user_name = "part" + "ner"
    assert legacy_user_name not in readme.lower()


def test_private_directory_is_gitignored() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "private/*" in gitignore
    assert "!private/.gitkeep" in gitignore
