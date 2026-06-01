# Job Alert Automation

Backend CLI and dashboard foundation for collecting job alert candidates from job alert emails.

The project started as a local/manual CLI. It now also contains a FastAPI dashboard boundary and a React dashboard foundation while the next auth-backed multi-user web app phases are staged explicitly.

## What Phase 1 Includes

- Manual CLI entrypoint with `--help`, `--dry-run`, `--run-now`, `--check-db`, and `--migrate`
- Two configured users: `minjian` and `chang`
- Non-secret user preferences in `backend/config/users.yaml`
- Secret-safe `.env` loading for `DATABASE_URL`
- Manual migration runner for SQL files in `backend/migrations/`
- Initial PostgreSQL schema for users, preferences, ingestion runs, emails, jobs, and user-job state
- URL/text normalization and in-memory job dedupe helpers
- Unit tests that do not require a real database

## Historical Phase 1 Deferrals

- LinkedIn, StepStone, and Indeed parsing
- Dashboard frontend work that now exists in the later frontend phases

Phase 2A adds readonly Gmail OAuth and metadata fetching only for the legacy fixed-user CLI flow. It still does not parse jobs, write Gmail changes, generate digests, or write ingestion data to the database.

Phase 2B adds parser and rule-filtering foundations in code and tests. It can parse LinkedIn, StepStone, and Indeed alert content into `ParsedJob` objects and mark likely relevance using configured keywords, locations, and exclusions.

Phase 2C adds real readonly dry-run previews. Phase 2D adds Neon persistence, batch-aware discovery tracking, and manual Codex analysis request/import files.

There is no scheduler, cron, GitHub Actions, browser-side AI call, or frontend-to-Neon connection in the current checkpoint.

## Web App Direction

UI-PUBLIC1 adds public frontend routing while keeping auth mock-only:

```text
/              Public landing page
/login         Google-only login page
/onboarding    Mock setup flow
/app/*         Mock-gated dashboard routes
/demo/*        Public mock-only dashboard preview
```

Google login and Gmail OAuth are separate:

- Future Google login identifies the app user.
- Gmail readonly authorization is a separate connection step for job alert email reading.
- Legacy `GOOGLE_TOKEN_MINJIAN` / `GOOGLE_TOKEN_CHANG` env paths exist only for fixed-user CLI token files. Web multi-user Gmail credentials are encrypted and stored behind FastAPI instead.

The preferred auth direction is Neon Auth with Google OAuth. AUTH1 adds a frontend Neon Auth mode behind the `AuthProvider` boundary while mock auth stays the default local fallback. AUTH2 adds a backend `/api/me` identity check for Neon Auth JWTs. AUTH3 adds an additive Neon Auth subject -> app user profile mapping and session-scoped dashboard reads. GMAIL-MU1 adds the authenticated Gmail readonly connect/status/disconnect boundary. GMAIL-MU2 adds manual fetch into the existing parser/dedupe/ingestion workflow. AI1 adds the backend-only Gemini analysis boundary and AI2 wires authenticated Jobs selection to it; scheduling stays staged.

Gemini analysis is backend-only. AI1 stores provider-tagged Gemini results from selected authenticated jobs through FastAPI, while manual Codex request/import remains the fallback. Configure backend AI analysis with `AI_PROVIDER`, `GEMINI_API_KEY`, `GEMINI_MODEL`, and `AI_ANALYSIS_MAX_JOBS` in the repository root `.env`. DOC2 lets authenticated Settings upload active profile Markdown and resume PDFs into private backend storage; Gemini prefers active profile Markdown and does not send resume PDFs by default. Browser code must never receive `GEMINI_API_KEY`, `DATABASE_URL`, Gmail OAuth tokens, or private document files.

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
cd backend
python -m pip install -e ".[dev]"
cd ..
```

Create a local `.env` file:

```bash
cp .env.example .env
```

Put your Neon PostgreSQL connection string in `.env` as `DATABASE_URL`. Do not commit `.env`; it is ignored by git. The CLI never prints the connection string.

## Test

```bash
cd backend
python -m pytest
```

## Frontend

Run the public landing, mock onboarding, demo dashboard, and dashboard routes locally:

```bash
cd frontend
npm install
npm run dev
```

Use `/demo` for mock-only public preview data. `/app/*` uses mock auth by default; frontend Neon Auth Google login is enabled only when the frontend is configured with `VITE_AUTH_MODE=neon` and `VITE_NEON_AUTH_URL`. Onboarding completion remains browser-session state until backend session/setup APIs land.

## Local Dashboard API

Phase F2 adds a read-only FastAPI layer for the dashboard. The frontend must use this API later instead of connecting directly to Neon.

Run the API locally:

```bash
cd backend
uvicorn api.app:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

Read-only endpoints:

```text
GET /api/users
GET /api/me
GET /api/user/preferences
PATCH /api/user/preferences
POST /api/onboarding/complete
GET /api/overview?user_id=minjian&range=latest_run
GET /api/jobs?user_id=minjian&range=latest_run
GET /api/jobs/{job_id}?user_id=minjian
GET /api/runs?user_id=minjian
PATCH /api/user-jobs/{job_id}/status
POST /api/analysis-requests
GET /api/gmail/status
POST /api/gmail/connect
GET /api/gmail/callback
POST /api/gmail/disconnect
POST /api/gmail/fetch
```

The API reads `DATABASE_URL` only from local environment or `.env`. It never returns the connection string to the browser. If the database is not configured, database-backed endpoints return a safe configuration error.

`GET /api/me` verifies a frontend Neon Auth JWT against the backend-only `NEON_AUTH_JWKS_URL` setting, provisions the additive app profile mapping when needed, and returns safe identity/profile metadata. Logged-in overview/jobs/runs requests use Bearer token ownership instead of the fixed `minjian`/`chang` selector path. Onboarding now saves auth-scoped role/location/exclusion preferences and completion state through the local API. The authenticated Settings page can start Gmail readonly OAuth, read safe connection status, disconnect stored Gmail authorization metadata, and run a manual Gmail fetch that creates an ingestion batch. DOC2 keeps profile/resume document actions behind the authenticated backend document boundary.

For split frontend/API deployments, set backend `API_CORS_ALLOWED_ORIGINS` to the explicit frontend origin list. Do not use wildcard origins for the authenticated dashboard path.

Status updates are the only F4 write operation. Valid status values are `new`, `saved`, `applied`, and `ignored`.

Analysis request preparation writes local Markdown/JSON files under `output/analysis_requests/` and creates an `analysis_batches` row. It does not call Codex or any AI API.

## Docker

Build the container:

```bash
docker compose build
```

Run tests in Docker:

```bash
docker compose run --rm app python -m pytest
```

Run Phase 1 placeholder dry runs in Docker:

```bash
docker compose run --rm app python -m job_alert_automation.main --dry-run
docker compose run --rm app python -m job_alert_automation.main --user minjian --dry-run
docker compose run --rm app python -m job_alert_automation.main --user chang --dry-run
```

Check the Neon database connection in Docker after adding `DATABASE_URL` to local `.env`:

```bash
docker compose run --rm app python -m job_alert_automation.main --check-db
```

Apply migrations manually in Docker:

```bash
docker compose run --rm app python -m job_alert_automation.main --migrate
```

Run the local FastAPI dashboard API in Docker:

```bash
docker compose up api
```

Run the frontend against the Docker API:

```bash
VITE_API_MODE=real VITE_API_BASE_URL=http://localhost:8000 docker compose up frontend
```

Docker Compose also reads root `.env` for frontend app auth configuration:

```text
VITE_AUTH_MODE=neon
VITE_NEON_AUTH_URL=...
NEON_AUTH_JWKS_URL=...
GMAIL_OAUTH_REDIRECT_URI=...
FRONTEND_BASE_URL=...
GMAIL_OAUTH_STATE_SECRET=...
GMAIL_TOKEN_ENCRYPTION_KEY=...
API_CORS_ALLOWED_ORIGINS=...
```

`VITE_NEON_AUTH_URL` is the public Neon Auth URL. `NEON_AUTH_JWKS_URL` is used by FastAPI to verify the JWT sent to `/api/me`. Gmail web OAuth redirect/state/encryption settings stay backend-only. None of these values is `DATABASE_URL`.

For local Neon Auth, open the frontend through one consistent origin. The recommended local origin is `http://localhost:5173`; set `FRONTEND_BASE_URL` to that same frontend origin before using Gmail OAuth. `GMAIL_OAUTH_REDIRECT_URI` must exactly match a redirect URI registered in the Google OAuth client.

Or start both API and frontend:

```bash
VITE_API_MODE=real VITE_API_BASE_URL=http://localhost:8000 docker compose up api frontend
```

Open:

```text
http://localhost:5173
```

The frontend still talks only to the local API. It never receives `DATABASE_URL`.

Deployment boundaries, secret tiers, OAuth callback checks, migrations, and current private-document storage requirements are tracked in [docs/deployment-plan.md](docs/deployment-plan.md).

Docker security notes:

- `.env` is used only at runtime by Docker Compose and is not copied into the image.
- `secrets/` is mounted into the container for future OAuth files and is not copied into the image.
- `output/` is mounted into the container for generated files and is not copied into the image.
- `private/` is mounted into the container for local profile files and is not copied into the image.
- Do not commit `.env`, Gmail OAuth files, tokens, passwords, or generated outputs.

## CLI Commands

Run local CLI commands from `backend/` after activating the repository virtual environment. Show help:

```bash
cd backend
python -m job_alert_automation.main --help
```

Run readonly dry-run previews:

```bash
python -m job_alert_automation.main --dry-run
python -m job_alert_automation.main --user minjian --dry-run
python -m job_alert_automation.main --user chang --dry-run
```

In Phase 2C, `--dry-run` performs a real readonly preview for authorized users:

- fetch Gmail full payloads with readonly scope
- extract message bodies without printing them
- parse LinkedIn, StepStone, and Indeed candidates
- deduplicate candidates in memory
- apply rule-based relevance filtering
- print a compact terminal summary
- perform no database writes

For an authorized single-user preview:

```bash
python -m job_alert_automation.main --user minjian --dry-run --max-results 5
```

Check the database connection after adding `DATABASE_URL` to `.env`:

```bash
python -m job_alert_automation.main --check-db
```

Apply migrations manually:

```bash
python -m job_alert_automation.main --migrate
```

Migrations are never applied automatically during `--dry-run` or `--run-now`.

Run real local/manual ingestion into Neon:

```bash
python -m job_alert_automation.main --user minjian --run-now --max-results 5
python -m job_alert_automation.main --user chang --run-now --max-results 5
```

Each real run creates one `ingestion_runs` batch and links seen jobs through `job_run_occurrences`.

## Gmail Readonly Setup

Phase 2A uses only this Gmail scope:

```text
https://www.googleapis.com/auth/gmail.readonly
```

The CLI does not delete, archive, label, mark as read, or otherwise modify emails.

Place your Google OAuth client JSON under `secrets/` and point `.env` at it:

```bash
GOOGLE_OAUTH_CLIENT_SECRETS_FILE=secrets/google_oauth_client.json
GOOGLE_TOKEN_MINJIAN=secrets/token_minjian.json
GOOGLE_TOKEN_CHANG=secrets/token_chang.json
```

Authorize each user locally:

```bash
python -m job_alert_automation.main --user minjian --authorize-gmail
python -m job_alert_automation.main --user chang --authorize-gmail
```

Fetch recent alert email metadata without parsing or database writes:

```bash
python -m job_alert_automation.main --user minjian --fetch-gmail
python -m job_alert_automation.main --user chang --fetch-gmail
python -m job_alert_automation.main --fetch-gmail --max-results 5
```

Fetch full readonly message payloads and extract body text for future parsing, without printing bodies or writing to the database:

```bash
python -m job_alert_automation.main --user minjian --fetch-gmail --include-body --max-results 5
python -m job_alert_automation.main --user chang --fetch-gmail --include-body --max-results 5
```

Docker can run metadata fetching after local OAuth token files exist:

```bash
docker compose run --rm app python -m job_alert_automation.main --user minjian --fetch-gmail
```

Parser and filtering logic currently runs through tests and will be wired into real ingestion in a later phase:

```bash
python -m pytest tests/test_email_parser.py tests/test_filters.py
```

## Codex Analysis Workflow

Codex analysis is the current manual fallback. Preparing and importing Codex files does not call OpenAI API, Gemini API, Codex API, or any AI API.

Status and discovery are separate:

- `status` is the user handling state: `new`, `saved`, `applied`, or `ignored`.
- Discovery is batch/time-based: newly discovered in a run, seen again in a run, or historical.

Private profile files are local only and gitignored:

```text
private/profiles/profile_minjian.md
private/profiles/profile_chang.md
```

Suggested private profile template:

```markdown
# Profile Summary

## Education

## Experience

## Skills

## Target Roles

## Preferred Locations

## Constraints

## Language Level

## Notes for Codex Analysis
```

If a profile file is missing, analysis request generation still works and falls back to non-secret preferences from `backend/config/users.yaml`.

Prepare an analysis request after jobs have been ingested:

```bash
python -m job_alert_automation.main --prepare-analysis --user minjian --latest-run --new-in-run-only
python -m job_alert_automation.main --prepare-analysis --user chang --since-days 7 --status new --not-analyzed-only
```

Docker:

```bash
docker compose run --rm app python -m job_alert_automation.main --prepare-analysis --user minjian --latest-run --new-in-run-only
```

The CLI writes:

```text
output/analysis_requests/latest_minjian.md
output/analysis_requests/latest_minjian.json
output/analysis_requests/analysis_minjian_<timestamp>.md
output/analysis_requests/analysis_minjian_<timestamp>.json
output/analysis_requests/latest_chang.md
output/analysis_requests/latest_chang.json
output/analysis_requests/analysis_chang_<timestamp>.md
output/analysis_requests/analysis_chang_<timestamp>.json
```

Open Codex manually and ask it to analyze:

```text
output/analysis_requests/latest_minjian.md
```

Save Codex result as:

```text
output/analysis_results/latest_minjian_result.json
```

Then import it:

```bash
python -m job_alert_automation.main --import-analysis output/analysis_results/latest_minjian_result.json
```

Docker:

```bash
docker compose run --rm app python -m job_alert_automation.main --import-analysis output/analysis_results/latest_minjian_result.json
```

Local API:

```bash
curl -X POST http://127.0.0.1:8000/api/analysis-import \
  -H "Content-Type: application/json" \
  -d '{"resultPath":"output/analysis_results/latest_minjian_result.json","overwrite":false}'
```

The dashboard import button uses this local API endpoint in real mode. The API only reads JSON files inside `output/analysis_results`.

Codex analysis consumes Codex usage in the separate Codex session. Future automated Gemini analysis will be backend-only and staged separately.

## Secrets

- `.env` is ignored by git.
- Everything inside `secrets/` is ignored except `secrets/.gitkeep`.
- Everything inside `output/` is ignored except `output/.gitkeep`.
- Everything inside `private/` stays local except the tracked placeholder files required by the repo.
- Do not commit database URLs, Gemini keys, Gmail OAuth client secrets, Gmail tokens, passwords, private documents, or generated outputs.
