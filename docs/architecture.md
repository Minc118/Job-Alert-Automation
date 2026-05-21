# Job Alert Automation Architecture

## System Overview

Job Alert Automation is a local/manual system for collecting job alert emails, storing parsed jobs in Neon PostgreSQL, preparing manual Codex analysis requests, and displaying results in a local dashboard.

The intended flow is:

```text
Gmail readonly alerts
  -> Backend CLI
  -> Neon PostgreSQL
  -> Future local backend API
  -> React dashboard
```

The frontend must never connect directly to Neon and must never receive `DATABASE_URL`, Gmail OAuth files, private profile files, resume PDFs, or API keys.

## Backend CLI Responsibilities

- Gmail readonly fetching.
- LinkedIn, StepStone, and Indeed alert parsing.
- Rule-based filtering and deduplication.
- Neon persistence via local `DATABASE_URL`.
- Ingestion run and batch tracking.
- Codex analysis request generation as local Markdown/JSON files.
- Codex structured JSON analysis import.

The CLI does not call OpenAI, Gemini, Codex, or any AI API.

## Future Local API Responsibilities

The future API will read Neon and return safe JSON to the dashboard.

Planned API responsibilities:

- Read overview metrics, jobs, ingestion runs, analysis data, users, and document metadata.
- Update `user_jobs.status`.
- Trigger preparation of Codex analysis request files.
- Import Codex analysis result JSON files.
- Manage local document metadata and upload/activation workflows.

The API must not expose secrets or private files as browser-readable URLs.

## Frontend Responsibilities

The React/Vite dashboard is initially a static mock. Later it will consume the local API only.

Frontend responsibilities:

- Display overview metrics and latest run summary.
- Display jobs with separate status and discovery filters.
- Display rule-based relevance and latest Codex analysis.
- Support local mock status changes in F1.
- Show mock Profile & Resume settings.
- Present prepare/import analysis actions as manual workflows.

The frontend must not connect to Neon directly and must not call any AI API.

## Neon Responsibilities

Neon PostgreSQL stores persistent metadata:

- Users and preferences.
- Email message metadata.
- Canonical jobs.
- User-job status and rule-match state.
- Ingestion runs.
- Job occurrences per run.
- Analysis batches.
- Codex job analyses.

Neon stores document metadata and local paths only. It must not store resume PDF binary content.

## Manual Codex Analysis Workflow

1. Jobs are fetched, parsed, deduplicated, and stored in Neon.
2. Each fetch creates an `ingestion_runs` batch.
3. Jobs seen in the run are linked through `job_run_occurrences`.
4. The CLI or future API prepares Markdown/JSON analysis request files.
5. The user opens Codex separately.
6. Codex reads the request file and local private profile files.
7. Codex returns structured JSON.
8. The CLI or future API imports that JSON into Neon.
9. The dashboard reads Neon via the local API and displays score, priority, reason, concern, suggested status, and links.

Codex usage is separate from this app. This project does not use OpenAI/Gemini API tokens.

## Status vs Discovery

Status is the user handling state:

- `new`: unprocessed
- `saved`
- `applied`
- `ignored`

Discovery is time/batch-based:

- `new_in_this_run`
- `seen_before`
- `historical`

A job can be `status = new` and `discovery = historical`. A job can be `discovery = new_in_this_run` and later `status = saved`.

## Users

Future-facing users:

- `minjian` / Minjian
- `chang` / Chang

Older database rows may contain legacy user data, but future-facing code, UI, mock data, and docs use Minjian and Chang.

## Private Profile And Resume Architecture

Private files stay local and gitignored:

```text
private/
  .gitkeep
  profiles/
    profile_minjian.md
    profile_chang.md
  resumes/
    resume_minjian.pdf
    resume_chang.pdf
  uploads/
    minjian/
    chang/
```

Future `user_documents` table:

- `id bigserial primary key`
- `user_id text not null references app_users(id) on delete cascade`
- `document_type text not null`
- `original_filename text not null`
- `stored_path text not null`
- `mime_type text`
- `file_size_bytes bigint`
- `is_active boolean not null default true`
- `created_at timestamptz default now()`

Document types:

- `profile_markdown`
- `resume_pdf`
- `cover_letter_template`

## Docker Usage

Existing Docker support remains backend-focused:

- `app`: backend CLI container.
- Future `api`: local API server.
- Future `frontend`: Vite dev server.

`.env`, `secrets/`, `private/`, and generated `output/` files must not be baked into images.

## Security Rules

- Never expose `DATABASE_URL` to the browser.
- Never expose Gmail OAuth client secrets or tokens.
- Never expose private profiles or resume PDFs as public URLs.
- Never add OpenAI API, Gemini API, or LLM provider abstractions.
- Keep Codex analysis manual or semi-manual.
