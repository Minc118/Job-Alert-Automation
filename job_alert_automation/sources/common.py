from __future__ import annotations

import re
from collections.abc import Iterable

from ..dedupe import normalize_text
from ..models import ParsedJob


URL_RE = re.compile(r"https?://[^\s<>()\"']+")

FIELD_ALIASES = {
    "title": "title",
    "job title": "title",
    "rolle": "title",
    "position": "title",
    "company": "company",
    "firma": "company",
    "unternehmen": "company",
    "employer": "company",
    "location": "location",
    "ort": "location",
    "standort": "location",
    "job location": "location",
    "url": "url",
    "link": "url",
    "job url": "url",
    "apply url": "url",
    "description": "description",
    "summary": "description",
    "beschreibung": "description",
}

NOISE_LINES = {
    "view job",
    "apply now",
    "bewerben",
    "job ansehen",
    "stellenanzeige ansehen",
    "unsubscribe",
    "abmelden",
}

NOISE_PREFIXES = (
    "alle jobs anzeigen",
    "andere jobs durchsuchen",
    "diese e-mail ist an ",
    "erfahren sie, warum wir dies hinzufügen",
    "indeed job-e-mail",
    "job-e-mail",
    "jobs bei ",
    "jobs für ",
    "jobs in ",
    "sie erhalten e-mails",
    "ähnliche jobs wie ",
    "weitere ähnliche jobs",
    "weitere aehnliche jobs",
)


def clean_lines(body: str | None) -> list[str]:
    if not body:
        return []
    lines = []
    cleaned_body = body.replace("\u00a0", " ")
    cleaned_body = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", cleaned_body)
    for line in cleaned_body.splitlines():
        cleaned = re.sub(r"[ \t\r\f\v]+", " ", line).strip(" \t-•|")
        if cleaned and not _is_noise(cleaned):
            lines.append(cleaned)
        else:
            lines.append("")
    return lines


def split_blocks(lines: Iterable[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if not line:
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)
    if current:
        blocks.append(current)
    return blocks


def _field_line(line: str) -> tuple[str, str] | None:
    match = re.match(r"^([A-Za-zÄÖÜäöüß ]{2,32})\s*:\s*(.+)$", line)
    if not match:
        return None
    raw_key, value = match.groups()
    key = FIELD_ALIASES.get(normalize_text(raw_key))
    if not key:
        return None
    value = value.strip()
    if not value:
        return None
    return key, value


def _clean_url(value: str | None) -> str | None:
    if not value:
        return None
    match = URL_RE.search(value)
    if not match:
        return None
    return match.group(0).rstrip(".,;")


def _is_noise(line: str) -> bool:
    normalized = normalize_text(line)
    return (
        normalized in NOISE_LINES
        or any(normalized.startswith(prefix) for prefix in NOISE_PREFIXES)
        or "passende ergebnisse auf indeed anzeigen" in normalized
        or re.search(r"\bjobs 1-\d+ von \d+", normalized) is not None
    )


def _job_from_fields(source: str, fields: dict[str, str], *, block_index: int) -> ParsedJob | None:
    title = fields.get("title")
    if not title:
        return None
    url = _clean_url(fields.get("url"))
    description = fields.get("description")
    return ParsedJob(
        source=source,
        title=title,
        company=fields.get("company"),
        location=fields.get("location"),
        url=url,
        short_description=description,
        metadata={"parser": "labeled_block", "block_index": block_index},
    )


def _job_from_position_block(source: str, block: list[str], *, block_index: int) -> ParsedJob | None:
    url = None
    content_lines: list[str] = []
    for line in block:
        found_url = _clean_url(line)
        if found_url and url is None:
            url = found_url
        stripped_without_url = URL_RE.sub("", line).strip()
        if stripped_without_url and not _is_noise(stripped_without_url):
            content_lines.append(stripped_without_url)

    if len(content_lines) < 2 or not url:
        return None

    title = content_lines[0]
    company = content_lines[1] if len(content_lines) > 1 else None
    location = content_lines[2] if len(content_lines) > 2 else None
    description = " ".join(content_lines[3:5]) if len(content_lines) > 3 else None
    return ParsedJob(
        source=source,
        title=title,
        company=company,
        location=location,
        url=url,
        short_description=description,
        metadata={"parser": "position_block", "block_index": block_index},
    )


def parse_alert_blocks(source: str, body: str | None) -> list[ParsedJob]:
    jobs: list[ParsedJob] = []
    for block_index, block in enumerate(split_blocks(clean_lines(body))):
        fields: dict[str, str] = {}
        unlabeled_lines: list[str] = []
        for line in block:
            parsed = _field_line(line)
            if parsed:
                key, value = parsed
                fields[key] = value
                continue
            unlabeled_lines.append(line)

        job = _job_from_fields(source, fields, block_index=block_index)
        if job is None:
            job = _job_from_position_block(source, unlabeled_lines or block, block_index=block_index)
        if job:
            jobs.append(job)
    return jobs
