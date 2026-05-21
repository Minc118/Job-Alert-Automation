from __future__ import annotations

import argparse
import sys
from pathlib import Path
from collections.abc import Sequence

from .analysis import AnalysisFilters, AnalysisValidationError, import_analysis_results, prepare_analysis_request
from .config import ConfigError, get_database_url, load_users_config
from .database import DatabaseError, check_connection
from .gmail_client import (
    GmailAuthRequired,
    GmailClientError,
    authorize_gmail_user,
    fetch_recent_alert_content,
    fetch_recent_alert_metadata,
)
from .ingestion import run_ingestion_for_user
from .migrations import apply_migrations
from .preview import build_dry_run_preview, format_dry_run_preview


PLACEHOLDER_MESSAGE = "Use --dry-run for preview or --run-now for database persistence."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m job_alert_automation.main",
        description="Backend-only manual CLI foundation for job alert automation.",
    )
    parser.add_argument("--user", help="Configured user id to process, for example: minjian or chang.")
    parser.add_argument("--check-db", action="store_true", help="Check the Neon PostgreSQL connection.")
    parser.add_argument("--migrate", action="store_true", help="Apply SQL migrations manually.")
    parser.add_argument("--dry-run", action="store_true", help="Validate configuration without database writes.")
    parser.add_argument("--run-now", action="store_true", help="Fetch, parse, dedupe, and store jobs manually.")
    parser.add_argument("--authorize-gmail", action="store_true", help="Authorize readonly Gmail access for one user.")
    parser.add_argument("--fetch-gmail", action="store_true", help="Fetch readonly Gmail alert messages. No parsing or DB writes.")
    parser.add_argument("--prepare-analysis", action="store_true", help="Prepare Markdown/JSON files for manual Codex analysis.")
    parser.add_argument("--import-analysis", help="Import a structured Codex analysis result JSON file into Neon.")
    parser.add_argument("--include-body", action="store_true", help="Fetch Gmail full payload and extract body text without printing it.")
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum Gmail messages to fetch per source query for --fetch-gmail.",
    )
    parser.add_argument("--limit", type=int, default=20, help="Maximum jobs for --prepare-analysis.")
    parser.add_argument("--status", choices=["new", "saved", "applied", "ignored"], help="Filter jobs by user handling status.")
    parser.add_argument("--latest-run", action="store_true", help="Filter analysis request jobs to the latest completed run.")
    parser.add_argument("--run-id", type=int, help="Filter analysis request jobs to a specific ingestion run id.")
    parser.add_argument("--since-days", type=int, help="Filter analysis request jobs seen within the last N days.")
    parser.add_argument("--new-in-run-only", action="store_true", help="Only include jobs newly discovered in the selected run.")
    parser.add_argument("--likely-relevant-only", action="store_true", help="Only include rule-based likely relevant jobs.")
    parser.add_argument("--not-analyzed-only", action="store_true", help="Only include jobs without stored Codex analysis.")
    parser.add_argument("--overwrite", action="store_true", help="Allow importing analysis for an already imported batch/job pair.")
    return parser


def _selected_action(args: argparse.Namespace) -> str | None:
    actions = {
        "check-db": args.check_db,
        "migrate": args.migrate,
        "dry-run": args.dry_run,
        "run-now": args.run_now,
        "authorize-gmail": args.authorize_gmail,
        "fetch-gmail": args.fetch_gmail,
        "prepare-analysis": args.prepare_analysis,
        "import-analysis": bool(args.import_analysis),
    }
    selected = [name for name, enabled in actions.items() if enabled]
    if not selected:
        return None
    if len(selected) > 1:
        raise ConfigError("Choose exactly one action.")
    return selected[0]


def _print_placeholder(mode: str, user_ids: list[str]) -> None:
    users = ", ".join(user_ids)
    print(f"Validated config for user(s): {users}.")
    print(f"Mode: {mode}.")
    print(PLACEHOLDER_MESSAGE)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        action = _selected_action(args)

        if action is None:
            parser.print_help()
            return 0

        if action == "check-db":
            database_url = get_database_url(required=True)
            check_connection(database_url)
            print("Database connection OK.")
            return 0

        if action == "migrate":
            database_url = get_database_url(required=True)
            result = apply_migrations(database_url)
            print(f"Migrations complete. Applied: {len(result.applied)}. Skipped: {len(result.skipped)}.")
            return 0

        config = load_users_config()
        user_ids = config.validate_user_id(args.user)

        if args.max_results < 1:
            raise ConfigError("--max-results must be at least 1.")

        if action == "authorize-gmail":
            if args.user is None:
                raise ConfigError("--authorize-gmail requires --user so tokens stay user-specific.")
            authorize_gmail_user(args.user)
            print(f"Gmail readonly authorization complete for user '{args.user}'.")
            return 0

        if action == "fetch-gmail":
            total = 0
            for user_id in user_ids:
                if args.include_body:
                    messages = fetch_recent_alert_content(user_id, max_results_per_source=args.max_results)
                else:
                    messages = fetch_recent_alert_metadata(user_id, max_results_per_source=args.max_results)
                total += len(messages)
                detail = "content" if args.include_body else "metadata"
                print(f"Fetched Gmail {detail} for user '{user_id}': {len(messages)} message(s).")
            print(f"Total Gmail message(s) fetched: {total}.")
            print("No email changes, parsing, digest generation, or database writes were performed.")
            return 0

        if action == "prepare-analysis":
            if args.user is None:
                raise ConfigError("--prepare-analysis requires --user.")
            database_url = get_database_url(required=True)
            filters = AnalysisFilters(
                limit=args.limit,
                status=args.status,
                latest_run=args.latest_run,
                run_id=args.run_id,
                since_days=args.since_days,
                new_in_run_only=args.new_in_run_only,
                likely_relevant_only=args.likely_relevant_only,
                not_analyzed_only=args.not_analyzed_only,
            )
            record = prepare_analysis_request(database_url, user_id=args.user, filters=filters)
            print(f"Analysis request prepared for user '{args.user}'.")
            print(f"Analysis batch id: {record.analysis_batch_id}.")
            print(f"Jobs included: {record.job_count}.")
            print(f"Markdown: {record.request_markdown_path}.")
            print(f"JSON: {record.request_json_path}.")
            print("No AI API was called.")
            return 0

        if action == "import-analysis":
            database_url = get_database_url(required=True)
            summary = import_analysis_results(
                database_url,
                result_path=Path(args.import_analysis),
                overwrite=args.overwrite,
            )
            print(f"Imported analyses: {summary.imported_count}.")
            print(f"Skipped analyses: {summary.skipped_count}.")
            print(f"Updated statuses: {summary.updated_statuses_count}.")
            print("No AI API was called.")
            return 0

        if action == "dry-run":
            processed_count = 0
            auth_error_count = 0
            for user_id in user_ids:
                try:
                    preview = build_dry_run_preview(user_id, max_results_per_source=args.max_results)
                except GmailAuthRequired:
                    if args.user is not None:
                        raise
                    auth_error_count += 1
                    print(
                        f"Skipping user '{user_id}': Gmail authorization is required.",
                        file=sys.stderr,
                    )
                    continue
                processed_count += 1
                print(format_dry_run_preview(preview))
            if processed_count == 0 and auth_error_count:
                return 1
            return 0

        if action == "run-now":
            database_url = get_database_url(required=True)
            processed_count = 0
            auth_error_count = 0
            for user_id in user_ids:
                try:
                    summary = run_ingestion_for_user(
                        database_url,
                        user_id=user_id,
                        max_results_per_source=args.max_results,
                    )
                except GmailAuthRequired:
                    if args.user is not None:
                        raise
                    auth_error_count += 1
                    print(
                        f"Skipping user '{user_id}': Gmail authorization is required.",
                        file=sys.stderr,
                    )
                    continue
                processed_count += 1
                print(f"Run {summary.ingestion_run_id} completed for user '{user_id}'.")
                print(f"  emails fetched: {summary.fetched_count}")
                print(f"  jobs parsed: {summary.parsed_count}")
                print(f"  unique jobs: {summary.unique_count}")
                print(f"  newly discovered: {summary.new_count}")
                print(f"  seen again: {summary.seen_again_count}")
                print(f"  likely relevant: {summary.likely_relevant_count}")
            if processed_count == 0 and auth_error_count:
                return 1
            return 0

        parser.error("Unsupported action.")
        return 2
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    except DatabaseError as exc:
        print(f"Database error: {exc}", file=sys.stderr)
        return 1
    except GmailAuthRequired as exc:
        print(f"Gmail authorization required: {exc}", file=sys.stderr)
        return 1
    except GmailClientError as exc:
        print(f"Gmail error: {exc}", file=sys.stderr)
        return 1
    except AnalysisValidationError as exc:
        print(f"Analysis import error: {exc}", file=sys.stderr)
        return 1
