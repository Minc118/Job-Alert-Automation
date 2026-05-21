from __future__ import annotations

from ..models import ParsedJob
from .common import parse_alert_blocks


def parse_linkedin_alert(body: str | None) -> list[ParsedJob]:
    return parse_alert_blocks("linkedin", body)
