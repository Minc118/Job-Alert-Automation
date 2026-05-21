from __future__ import annotations

from collections.abc import Iterable

from .dedupe import normalize_text
from .models import JobFilterResult, ParsedJob, UserPreferences


def _contains_phrase(haystack: str, phrase: str) -> bool:
    normalized_phrase = normalize_text(phrase)
    if not normalized_phrase:
        return False
    if normalized_phrase in haystack:
        return True
    phrase_tokens = tuple(token for token in normalized_phrase.split() if len(token) > 1)
    return bool(phrase_tokens) and all(token in haystack for token in phrase_tokens)


def _job_haystack(job: ParsedJob) -> str:
    return normalize_text(
        " ".join(
            value
            for value in (
                job.title,
                job.company,
                job.location,
                job.short_description,
            )
            if value
        )
    )


def _matched_terms(haystack: str, terms: Iterable[str]) -> tuple[str, ...]:
    return tuple(term for term in terms if _contains_phrase(haystack, term))


def evaluate_job_relevance(job: ParsedJob, preferences: UserPreferences) -> JobFilterResult:
    haystack = _job_haystack(job)
    matched_keywords = _matched_terms(haystack, preferences.target_role_keywords)
    matched_locations = _matched_terms(haystack, preferences.preferred_locations)
    exclusion_matches = _matched_terms(haystack, preferences.excluded_keywords)

    has_keyword_match = bool(matched_keywords)
    has_location_match = bool(matched_locations) or not preferences.preferred_locations
    likely_relevant = has_keyword_match and has_location_match and not exclusion_matches

    reason_parts: list[str] = []
    if matched_keywords:
        reason_parts.append("matched role keyword(s): " + ", ".join(matched_keywords))
    if matched_locations:
        reason_parts.append("matched location(s): " + ", ".join(matched_locations))
    if exclusion_matches:
        reason_parts.append("excluded by keyword(s): " + ", ".join(exclusion_matches))
    if not reason_parts:
        reason_parts.append("no configured role or location keywords matched")

    return JobFilterResult(
        job=job,
        likely_relevant=likely_relevant,
        matched_keywords=matched_keywords,
        matched_locations=matched_locations,
        exclusion_matches=exclusion_matches,
        relevance_reason="; ".join(reason_parts),
    )


def evaluate_jobs_relevance(
    jobs: Iterable[ParsedJob],
    preferences: UserPreferences,
) -> list[JobFilterResult]:
    return [evaluate_job_relevance(job, preferences) for job in jobs]
