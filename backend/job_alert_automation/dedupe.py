from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .models import DedupeKey, ParsedJob


TRACKING_QUERY_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "msclkid",
}


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", value)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_url(url: str | None) -> str | None:
    if not url or not url.strip():
        return None

    raw = url.strip()
    parsed = urlsplit(raw)
    if not parsed.scheme and not parsed.netloc and "." in parsed.path.split("/", 1)[0]:
        parsed = urlsplit(f"https://{raw}")

    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or ""

    query_items = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in TRACKING_QUERY_PARAMS
    ]
    query_items.sort(key=lambda item: (item[0].lower(), item[1]))
    query = urlencode(query_items, doseq=True)

    return urlunsplit((scheme, netloc, path, query, ""))


def hash_normalized_url(normalized_url: str | None) -> str | None:
    if not normalized_url:
        return None
    return hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()


def build_job_dedupe_key(job: ParsedJob) -> DedupeKey:
    source = normalize_text(job.source)
    normalized_url = normalize_url(job.url)
    normalized_url_hash = hash_normalized_url(normalized_url)

    if normalized_url_hash:
        return DedupeKey(
            kind="url",
            source=source,
            value=normalized_url_hash,
            parts=(source, normalized_url_hash),
        )

    normalized_title = normalize_text(job.title)
    normalized_company = normalize_text(job.company)
    normalized_location = normalize_text(job.location)
    parts = (source, normalized_title, normalized_company, normalized_location)
    return DedupeKey(
        kind="fallback",
        source=source,
        value="|".join(parts),
        parts=parts,
    )


def dedupe_jobs(jobs: Sequence[ParsedJob]) -> tuple[list[ParsedJob], dict[str, int]]:
    seen: set[DedupeKey] = set()
    unique_jobs: list[ParsedJob] = []

    for job in jobs:
        key = build_job_dedupe_key(job)
        if key in seen:
            continue
        seen.add(key)
        unique_jobs.append(job)

    return unique_jobs, {
        "input_count": len(jobs),
        "unique_count": len(unique_jobs),
        "duplicate_count": len(jobs) - len(unique_jobs),
    }


def find_existing_job_ids(_connection, _keys: Sequence[DedupeKey]) -> dict[DedupeKey, int]:
    """Future database lookup hook for Phase 2 ingestion dedupe checks."""
    raise NotImplementedError("Database dedupe lookups will be implemented with ingestion in Phase 2.")
