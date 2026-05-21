# Job Alert Automation Architecture

## Current Checkpoint

The repository currently contains:

- A Python CLI for Gmail readonly fetch, parsing, dedupe, ingestion batches, and manual Codex analysis files.
- A FastAPI backend layer for dashboard reads plus staged status and manual analysis workflows.
- A React/Vite dashboard with mock and local API modes.
- A profile/resume frontend and document architecture foundation that still needs auth-scoped hardening later.
- Local Docker support for backend CLI/API and frontend development.

UI-PUBLIC1 adds public frontend routing and mock auth/onboarding structure. AUTH0 refines that structure into a documented auth boundary and a replaceable frontend auth seam. It does not add real authentication, backend sessions, Gemini runtime calls, or multi-user Gmail OAuth.

## Target System

The product is evolving from a local personal tool into a small multi-user web app:

```text
Public Landing / Login
  -> Google app authentication
  -> Onboarding
  -> React dashboard
  -> Local or deployed FastAPI backend
  -> Neon PostgreSQL
```

The dashboard must never connect directly to Neon. Browser code must never receive `DATABASE_URL`, Gmail OAuth client secrets, Gmail tokens, Gemini keys, private profile files, or resume PDFs.

## Frontend Flows

Public routes are:

- `/` for the landing page.
- `/login` for Google-only login copy.
- `/demo/*` for mock-only dashboard preview data.

Authenticated target routes are:

- `/onboarding`
- `/app/overview`
- `/app/jobs`
- `/app/settings`

AUTH0 keeps mock auth and onboarding state in `sessionStorage` through a frontend `AuthProvider` seam. It stores browser-session mock state only and persists onboarding progress so route behavior can be exercised without real Neon Auth. Real session handling is deferred to AUTH1-AUTH3.

## Authentication And Gmail

Google login and Gmail OAuth are separate flows.

- Google login identifies the app user.
- Gmail OAuth grants readonly access to job alert emails after the user chooses to connect Gmail.
- Gmail UI copy must not imply that login alone grants mailbox access.
- Gmail readonly access must not send, delete, archive, or mark email as read.

Preferred authentication direction is Neon Auth with Google OAuth if it proves suitable. The project does not add email/password registration, password reset, password hashes, or a custom password login system in this direction.

The detailed AUTH0 boundary, identity mapping direction, and `/api/me` staging are documented in [`docs/auth0-auth-architecture.md`](auth0-auth-architecture.md).

## Backend CLI Responsibilities

The CLI remains useful for local/manual workflows:

- Gmail readonly fetching.
- LinkedIn, StepStone, and Indeed alert parsing.
- Rule-based filtering and deduplication.
- Neon persistence through local `DATABASE_URL`.
- Ingestion run and batch tracking.
- Manual Codex request generation and JSON result import.

## Backend API Responsibilities

FastAPI is the dashboard boundary. Current API work keeps frontend data access behind safe JSON endpoints. Staged future API work adds:

- Session/user identity via `/api/me`.
- Auth-scoped preferences.
- User-job status actions.
- Gmail connection/fetch status.
- Gemini analysis orchestration.
- Analysis batch reads and manual Codex fallback.
- Auth-scoped document metadata and file operations.

The API may load private files on the backend where authorized. It must not expose private filesystem paths as direct browser-readable URLs.

## Dashboard Responsibilities

The dashboard keeps one central jobs workspace:

- Overview metrics, latest run summary, recent activity, and top recommendations.
- Jobs table, filters, detail drawer, status actions, analysis output, and application prompt copy.
- Settings for preferences, documents, data sources, and Gmail connection state.

The frontend talks only to backend clients. Demo mode must use mock data even when real API mode is configured.

## Neon Responsibilities

Neon stores persistent app data and metadata:

- `app_users`
- `user_preferences`
- `ingestion_runs`
- `email_messages`
- `jobs`
- `user_jobs`
- `job_run_occurrences`
- `analysis_batches`
- `codex_job_analyses`
- `user_documents`

Future auth-backed profile mapping and Gmail token storage need additive migrations that preserve existing data. Resume PDF binaries stay outside Neon; Neon stores document metadata and safe stored paths.

## Analysis Direction

Manual Codex import remains the fallback path:

1. CLI or API prepares Markdown/JSON analysis request files.
2. User opens Codex separately.
3. Codex returns structured JSON.
4. CLI or API validates and imports results into Neon.

Gemini becomes the future primary automated analysis path, but it is backend-only:

1. User selects jobs.
2. Frontend asks the backend to run Gemini analysis.
3. Backend validates ownership and loads compact active profile summary data.
4. Backend sends compact job fields to Gemini and validates strict JSON output.
5. Backend stores score, priority, reason, concern, suggested status, provider, and analysis batch metadata.

Raw Gmail email bodies and full resume PDFs are not sent to Gemini by default. The frontend must never call Gemini directly.

## Status Vs Discovery

Status is the user handling state:

- `new`: unprocessed
- `saved`
- `applied`
- `ignored`

Discovery is time and batch state:

- `new_in_this_run`
- `seen_before`
- `historical`

A job can be `status = new` and `discovery = historical`. Newly discovered work is filtered from ingestion run data, not from the status field.

## Users And Isolation

Future-facing development identities remain:

- `minjian` / Minjian
- `chang` / Chang

Auth migration must map browser session identity to backend-owned user data and enforce ownership checks for jobs, runs, analyses, documents, preferences, and Gmail connections. Legacy fixed-user rows should be preserved until an explicit migration handles them.

## Private Documents

Private files stay outside public frontend assets and remain gitignored:

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

Document types are `profile_markdown`, `resume_pdf`, and `cover_letter_template`.

- Active profile summaries are the preferred analysis context.
- Resume PDFs are reserved for later application material work unless a future explicit policy changes that.
- Frontend components receive safe metadata through API responses only.

## Docker And Security

Existing Docker support stays compatible with backend CLI/API and frontend development. `.env`, `secrets/`, `private/`, and generated `output/` files must not be baked into images.

Security invariants:

- Do not expose `DATABASE_URL`, Gmail OAuth secrets/tokens, Gemini keys, or private documents.
- Keep frontend -> backend -> Neon as the data path.
- Use Google login and Gmail OAuth as separate authorization concepts.
- Add backend auth, Gmail, and Gemini runtime behavior only in staged phases.
