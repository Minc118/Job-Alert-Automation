# Job Alert Automation Backend

Python CLI and FastAPI backend for the Job Alert Automation repository.

Run backend commands from this directory:

```bash
cd backend
```

Install the editable backend with development dependencies:

```bash
python -m pip install -e ".[dev]"
```

The default `.env` remains at the repository root. Root-level `secrets/`, `private/`, and `output/` directories remain the runtime file locations.

For AUTH2 backend identity verification, add `NEON_AUTH_JWKS_URL` to the root `.env`. `/api/me` validates Neon Auth Bearer JWTs against that JWKS endpoint and returns safe identity metadata only.

FastAPI accepts the local Vite origins by default. For any split-origin deployment, set backend-only `API_CORS_ALLOWED_ORIGINS` in root `.env` or the runtime secret/config store to an explicit comma-separated frontend origin allowlist.

For GMAIL-MU1 web Gmail readonly connection, keep Google OAuth client secrets under root `secrets/` and add backend-only root `.env` values for:

```text
GMAIL_OAUTH_REDIRECT_URI
FRONTEND_BASE_URL
GMAIL_OAUTH_STATE_SECRET
GMAIL_TOKEN_ENCRYPTION_KEY
```

The Settings UI receives status metadata only. Gmail OAuth client secrets and encrypted Google credentials stay on the backend side.

`GOOGLE_TOKEN_MINJIAN` and `GOOGLE_TOKEN_CHANG` remain legacy fixed-user CLI token paths. The web multi-user Gmail path does not add one token env variable per app user.

GMAIL-MU2 adds an authenticated manual fetch endpoint at `POST /api/gmail/fetch`. It reuses the existing parser, dedupe, relevance filter, and ingestion batch persistence path; it does not add scheduling.

AI1 adds a backend-only Gemini analysis endpoint at `POST /api/analysis/run`. It requires the Neon Auth Bearer identity, validates selected job ownership, sends compact preference and job fields only, validates structured JSON, and stores provider-tagged analysis rows. Keep `GEMINI_API_KEY` in the repository root `.env`; it is never sent to frontend code.

DOC2 adds auth-scoped private document endpoints under `/api/user/documents`. Profile summaries and cover letter templates accept UTF-8 Markdown, resume uploads accept PDF, and the API returns metadata plus Markdown preview text only. Private stored paths and resume PDF bytes are not browser responses.

Run tests:

```bash
python -m pytest
```

Run the CLI:

```bash
python -m job_alert_automation.main --help
python -m job_alert_automation.main --dry-run
python -m job_alert_automation.main --check-db
python -m job_alert_automation.main --migrate
```

Run the FastAPI server:

```bash
uvicorn api.app:app --reload --host 127.0.0.1 --port 8000
```

Docker Compose stays rooted at the repository root:

```bash
docker compose build
docker compose run --rm app python -m pytest
```
