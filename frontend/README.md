# Job Alert Dashboard Frontend

Dashboard for the local/manual Job Alert Automation system.

## Scope

- React, Vite, TypeScript, and Tailwind CSS.
- Mock mode by default; real local API mode is available for dashboard integration.
- Public landing, Google-only login copy, mock onboarding, guarded dashboard routes, and mock-only demo routes.
- No direct Neon connection.
- No browser-side OpenAI API, Gemini API, Codex API, Gmail token, or database credential use.
- Document data stays behind backend APIs; public onboarding upload controls remain mock-only in UI-PUBLIC1.

## Commands

```bash
npm install
npm run dev
npm run build
```

## Mock Mode

Mock mode is the default and does not require the backend API:

```bash
cd frontend
npm run dev
```

Important routes:

```text
/              Public landing
/login         Google-only mock login
/onboarding    Mock onboarding flow
/app/overview  Mock-gated dashboard
/demo          Public mock-only dashboard preview
```

AUTH0 exposes a future-friendly `AuthProvider` seam backed by mock Google sign-in and onboarding state in `sessionStorage` for the current browser session only.

You can also make it explicit:

```bash
cp .env.example .env
# keep VITE_API_MODE=mock
npm run dev
```

## Real API Mode

Start the local FastAPI server from the backend directory:

```bash
cd "/Users/min/Desktop/playground/Job Alert Automation/backend"
source ../.venv/bin/activate
uvicorn api.app:app --reload --host 127.0.0.1 --port 8000
```

Then configure the frontend:

```bash
cd frontend
cp .env.example .env
```

Set:

```text
VITE_API_MODE=real
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Run:

```bash
npm run dev
```

If the API is unavailable, the dashboard shows a safe error message. It never receives `DATABASE_URL` or connects directly to Neon.

In real mode, the dashboard can:

- Read overview, jobs, runs, and job detail data through the local API.
- Update user job status through the local API.
- Prepare Codex analysis request files through the local API.
- Import Codex analysis result JSON from `output/analysis_results` through the local API and refresh latest analysis data.

It still does not call OpenAI, Gemini, Codex, or any AI API.

## Public Flow Direction

Google app login and Gmail readonly authorization stay separate:

- Google login will identify the app user in later AUTH phases.
- Gmail connection remains a later explicit job-alert mailbox authorization step.

The detailed AUTH0 direction is documented in `../docs/auth0-auth-architecture.md`. Real Neon Auth and backend session validation stay staged for later phases.

Gemini analysis is a later backend-only workflow. Manual Codex prepare/import remains available through current backend paths.

## Docker

From the repository root:

```bash
VITE_API_MODE=real VITE_API_BASE_URL=http://127.0.0.1:8000 docker compose up api frontend
```

Then open:

```text
http://127.0.0.1:5173
```

The Docker frontend service talks to the local API on port `8000`; it does not receive Neon credentials.

The future production data path is:

```text
React Dashboard -> Local Backend API -> Neon PostgreSQL
```

The manual Codex flow remains file-based: prepare analysis request, open Codex separately, save structured JSON, then import it through the backend CLI or API.
