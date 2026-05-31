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

AUTH1 keeps the `AuthProvider` seam and uses mock Google sign-in by default. Mock sign-in and onboarding state live in `sessionStorage` for the current browser session only.

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

## Neon Auth Frontend Mode

AUTH1 can start app login through Neon Auth from Landing and Login pages.

Configure the frontend:

```bash
cp .env.example .env
```

Set:

```text
VITE_AUTH_MODE=neon
VITE_NEON_AUTH_URL=https://your-neon-auth-url
```

The Auth URL is frontend configuration, not `DATABASE_URL`. Configure your Neon Auth trusted origins for the local frontend origin you use, for example the Vite dev origin.

For Docker Compose, put the same frontend auth variables in the repository root `.env`; Compose passes them into the frontend container.

Neon Auth with AUTH3 remains staged but account-scoped:

- Login identifies the app user.
- Job preferences and onboarding completion are saved through authenticated FastAPI endpoints.
- FastAPI `/api/me` can validate the Neon Auth JWT when backend `NEON_AUTH_JWKS_URL` is configured.
- AUTH3 maps the Neon Auth subject to a backend-owned app profile and uses Bearer-authenticated overview/jobs/runs reads.
- GMAIL-MU1 lets authenticated Settings start Gmail readonly OAuth, show safe connection status, and disconnect Gmail metadata through FastAPI.
- GMAIL-MU2 lets authenticated Settings run a manual Gmail fetch and refresh dashboard data through FastAPI.
- AI1/AI2 let authenticated Jobs selections call backend-only Gemini analysis and refresh stored results through FastAPI.
- DOC2 lets authenticated Settings upload, activate, preview Markdown, and delete private profile/resume documents through FastAPI metadata endpoints.
- Existing fixed `user_id` development paths remain for local compatibility, but the public demo and Neon-authenticated `/app/*` views do not expose real personal identity switchers.

## Public Flow Direction

Google app login and Gmail readonly authorization stay separate:

- Google login identifies the app user.
- Gmail connection is an explicit job-alert mailbox authorization step through FastAPI.
- The browser never handles legacy fixed-user token file paths such as `GOOGLE_TOKEN_*`.

The detailed AUTH0-AUTH3 direction is documented in `../docs/auth0-auth-architecture.md`. Gmail fetch/ingestion, documents, and AI orchestration continue as staged backend work.

Gemini analysis is backend-only. Authenticated Jobs can run it through FastAPI; manual Codex prepare/import remains available through current backend paths.

## Docker

From the repository root:

```bash
VITE_API_MODE=real VITE_API_BASE_URL=http://localhost:8000 docker compose up api frontend
```

Then open:

```text
http://localhost:5173
```

The Docker frontend service talks to the local API on port `8000`; it does not receive Neon credentials. Keep the frontend origin consistent for local Neon Auth; use `http://localhost:5173` with `FRONTEND_BASE_URL=http://localhost:5173` before testing Gmail OAuth.

The future production data path is:

```text
React Dashboard -> FastAPI backend -> Neon PostgreSQL
```

For deployed real API mode, `VITE_API_BASE_URL` is the public FastAPI origin. The backend separately needs an explicit `API_CORS_ALLOWED_ORIGINS` allowlist for the deployed frontend origin. Do not put backend secrets into any `VITE_*` setting.

The manual Codex flow remains file-based: prepare analysis request, open Codex separately, save structured JSON, then import it through the backend CLI or API. Deployment planning lives in `../docs/deployment-plan.md`.
