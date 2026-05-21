from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AppUser:
    id: str
    display_name: str
    email: str | None = None


@dataclass(frozen=True)
class UserPreferences:
    user_id: str
    target_role_keywords: tuple[str, ...] = ()
    preferred_locations: tuple[str, ...] = ()
    excluded_keywords: tuple[str, ...] = ()
    source_queries: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class EmailMessageMetadata:
    user_id: str
    gmail_message_id: str
    gmail_thread_id: str | None = None
    source: str | None = None
    sender: str | None = None
    subject: str | None = None
    received_at: datetime | None = None
    snippet: str | None = None
    body_hash: str | None = None


@dataclass(frozen=True)
class EmailMessageContent:
    metadata: EmailMessageMetadata
    text_body: str | None = None
    html_body: str | None = None
    body_hash: str | None = None


@dataclass(frozen=True)
class ParsedJob:
    source: str
    title: str
    company: str | None = None
    location: str | None = None
    url: str | None = None
    short_description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class JobFilterResult:
    job: ParsedJob
    likely_relevant: bool
    matched_keywords: tuple[str, ...] = ()
    matched_locations: tuple[str, ...] = ()
    exclusion_matches: tuple[str, ...] = ()
    relevance_reason: str | None = None


@dataclass(frozen=True)
class DedupeKey:
    kind: str
    source: str
    value: str
    parts: tuple[str, ...]


@dataclass(frozen=True)
class RunSummary:
    mode: str
    selected_user_id: str | None = None
    fetched_count: int = 0
    parsed_count: int = 0
    new_count: int = 0
    duplicate_count: int = 0
    filtered_count: int = 0
    status: str = "started"
    output_markdown_path: str | None = None
    output_json_path: str | None = None
    error_message: str | None = None
