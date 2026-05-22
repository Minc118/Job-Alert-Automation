# Job Alert Automation Architecture

## Current Checkpoint

The repository currently contains:

- A Python CLI for Gmail readonly fetch, parsing, dedupe, ingestion batches, and manual Codex analysis files.
- A FastAPI backend layer for dashboard reads, status/manual analysis workflows, Neon-authenticated ownership, Gmail readonly connect/fetch, Gemini analysis, and private document metadata.
- A React/Vite dashboard with mock and local API modes.
- Auth-scoped profile/resume private document handling through backend APIs.
- Local Docker support for backend CLI/API and frontend development.

UI-PUBLIC1 adds public frontend routing and mock auth/onboarding structure. AUTH0 refines that structure into a documented auth boundary and a replaceable frontend auth seam. AUTH1 adds the frontend Neon Auth Google login foundation behind that seam. AUTH2 adds FastAPI JWT/JWKS identity validation through `/api/me`. AUTH3 adds additive auth-subject app profile mapping plus session-scoped overview/jobs/runs reads. ONBOARD1 persists auth-scoped preference setup. GMAIL-MU1 starts the authenticated Gmail readonly connection boundary. GMAIL-MU2 adds manual fetch and ingestion for the mapped app user. AI1/AI2 add backend-only Gemini analysis and authenticated Jobs triggering. DOC2 adds auth-scoped document handling. Background scheduling stays staged.

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

The frontend auth seam supports two current modes:

- `mock` by default for local/demo work, with browser-session mock sign-in state.
- `neon` when `VITE_AUTH_MODE=neon` and a public `VITE_NEON_AUTH_URL` are configured.

AUTH1 Neon mode starts Google login in Neon Auth and reads frontend session state from the Neon SDK. AUTH2 verifies Neon Auth JWTs in FastAPI through backend `NEON_AUTH_JWKS_URL`. AUTH3 provisions a private app user id for each Neon Auth subject and uses that mapping for authenticated overview/jobs/runs reads. ONBOARD1 stores auth-scoped target roles, preferred locations, excluded keywords, and onboarding completion. GMAIL-MU1 uses that mapped app user for Gmail readonly connect/status/disconnect. GMAIL-MU2 performs a user-triggered fetch with those credentials and persists the resulting ingestion batch.

The Neon-authenticated `/app/*` view does not expose the fixed `minjian`/`chang` development user switcher. Fixed-user query paths stay compatible for local/manual development, while Bearer-authenticated requests use the mapped app profile. The public `/demo/*` route remains the mock dashboard preview path.

## Authentication And Gmail

Google login and Gmail OAuth are separate flows.

- Google login identifies the app user.
- Gmail OAuth grants readonly access to job alert emails after the user chooses to connect Gmail.
- Gmail UI copy must not imply that login alone grants mailbox access.
- Gmail readonly access must not send, delete, archive, or mark email as read.

Preferred authentication direction is Neon Auth with Google OAuth if it proves suitable. The project does not add email/password registration, password reset, password hashes, or a custom password login system in this direction.

The detailed AUTH0 boundary, identity mapping direction, and `/api/me` staging are documented in [`docs/auth0-auth-architecture.md`](auth0-auth-architecture.md).

DEPLOY1 keeps deployment planning explicit in [`docs/deployment-plan.md`](deployment-plan.md): frontend/public variables, backend secrets, OAuth callbacks, Neon migrations, CORS allowlists, and current private document storage requirements.

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

- Session/user identity via the implemented `/api/me` JWT/JWKS check.
- Auth-scoped preferences.
- User-job status actions.
- Gmail connection/fetch status.
- Manual Gmail fetch into the existing parser/dedupe/batch workflow.
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
- `app_user_profiles`
- `gmail_oauth_connections`

Resume PDF binaries stay outside Neon; Neon stores document metadata and safe stored paths. Gmail OAuth credentials are stored only by the backend in encrypted form, keyed by the mapped app user.

AUTH3 adds `app_user_profiles` as the first auth mapping layer. It keeps existing `app_users` rows and creates separate auth-backed `app_users` rows for Neon Auth subjects instead of reusing fixed development identities by browser choice. GMAIL-MU1 adds `gmail_oauth_connections` without changing the legacy CLI token files used by fixed local users.

## Analysis Direction

Manual Codex import remains the fallback path:

1. CLI or API prepares Markdown/JSON analysis request files.
2. User opens Codex separately.
3. Codex returns structured JSON.
4. CLI or API validates and imports results into Neon.

Gemini becomes the primary automated analysis path in staged backend work, and it is backend-only:

1. User selects jobs.
2. Frontend asks the backend to run Gemini analysis.
3. Backend validates ownership and loads compact analysis context. AI1 uses auth-scoped preferences; active profile document loading stays staged with document hardening.
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
- DOC2 stores uploaded binaries under private backend storage and records metadata in `user_documents`.
- Authenticated frontend components receive safe metadata and Markdown preview text through API responses only; they do not receive private stored paths or PDF bytes.

## Docker And Security

Existing Docker support stays compatible with backend CLI/API and frontend development. `.env`, `secrets/`, `private/`, and generated `output/` files must not be baked into images.

Security invariants:

- Do not expose `DATABASE_URL`, Gmail OAuth secrets/tokens, Gemini keys, or private documents.
- Keep frontend -> backend -> Neon as the data path.
- Keep API CORS origins as an explicit deployed frontend allowlist for browser Bearer requests.
- Use Google login and Gmail OAuth as separate authorization concepts.
- Add backend auth, Gmail, and Gemini runtime behavior only in staged phases.
