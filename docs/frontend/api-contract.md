# Frontend API Contract

The browser data path is always:

```text
React frontend -> FastAPI backend -> Neon PostgreSQL
```

The frontend never receives Neon connection strings, Gmail OAuth secrets/tokens, Gemini credentials, or private document contents.

## Current Endpoint Status

Implemented backend work through the current dashboard phases includes the current read APIs plus staged status and manual analysis support:

- `GET /api/health`
- `GET /api/users`
- `GET /api/me`
- `GET /api/user/preferences`
- `PATCH /api/user/preferences`
- `POST /api/onboarding/complete`
- `GET /api/overview?user_id=minjian&range=latest_run`
- `GET /api/jobs?user_id=minjian&range=latest_run`
- `GET /api/jobs/{job_id}?user_id=minjian`
- `GET /api/runs?user_id=minjian`
- `PATCH /api/user-jobs/{job_id}/status`
- `POST /api/analysis-requests`
- `POST /api/analysis-import`
- `GET /api/gmail/status`
- `POST /api/gmail/connect`
- `GET /api/gmail/callback`
- `POST /api/gmail/disconnect`
- `POST /api/gmail/fetch`

UI-PUBLIC1, AUTH0, and AUTH1 do not add backend runtime endpoints. AUTH1 only adds frontend Neon Auth session foundation behind the existing auth seam. AUTH2 adds `/api/me` as the first session validation endpoint. AUTH3 adds auth-backed app profile mapping and bearer-token read variants for overview/jobs/runs. GMAIL-MU1 adds the authenticated Gmail readonly connection boundary. GMAIL-MU2 adds authenticated manual Gmail fetch and reuses ingestion batches for the mapped app user.

## Session And Auth Direction

`GET /api/me`

Validates a Neon Auth Bearer JWT against backend `NEON_AUTH_JWKS_URL` and returns safe identity metadata for the authenticated browser user. Current shape:

```json
{
  "authenticated": true,
  "authProvider": "neon",
  "user": {
    "subject": "auth-subject",
    "displayName": "Signed In User",
    "email": "user@example.com"
  },
  "appUser": {
    "id": "auth_backend_owned_user_id",
    "displayName": "Signed In User"
  },
  "accountDataReady": true,
  "onboardingComplete": false
}
```

Google app login and Gmail OAuth are separate. Session routes must not imply mailbox authorization.

Once backend sessions exist, owned-resource endpoints should prefer session-derived ownership over trusting browser-provided `user_id` query parameters.

With AUTH3, requests with a valid Bearer token can omit `user_id` for overview, jobs, job detail, runs, and user-job status changes. FastAPI derives the mapped app user from the JWT subject. Existing fixed development `user_id` query/body paths remain for current local CLI/dashboard compatibility.

## Users And Preferences

Current:

`GET /api/users`

Current authenticated onboarding setup:

- `GET /api/user/preferences`
- `PATCH /api/user/preferences`
- `POST /api/onboarding/complete`

Preferences responses remain safe user-facing data: target keywords, preferred locations, excluded keywords, and source query metadata that the frontend is allowed to display.

## Overview

`GET /api/overview?user_id=minjian&range=latest_run`

Returns overview counters, latest run summary, source summary, recent activity, and top recommended jobs. Auth-backed versions should derive user identity from the session where possible.

## Jobs

- `GET /api/jobs?user_id=minjian&range=latest_run&status=new`
- `GET /api/jobs/{job_id}?user_id=minjian`
- `PATCH /api/user-jobs/{job_id}/status`

Jobs responses stay aligned with frontend job types:

- application handling `status`
- batch/time `discovery`
- source/application link
- rule-based relevance
- latest analysis data
- run metadata needed by the table and drawer

Valid status values are `new`, `saved`, `applied`, and `ignored`. Status changes must not rewrite discovery.

## Runs

`GET /api/runs?user_id=minjian`

Returns ingestion run summaries for latest-run and time-range dashboard views.

## Documents

Current DOC2 authenticated endpoints:

- `GET /api/user/documents`
- `POST /api/user/documents`
- `PATCH /api/user/documents/{document_id}/activate`
- `DELETE /api/user/documents/{document_id}`
- `GET /api/user/documents/{document_id}/preview`

Document endpoints require the Neon Auth Bearer identity and scope operations through the mapped backend app user. Uploads use multipart form fields `documentType` and `file`. Responses expose safe metadata only; stored private paths and resume PDF bytes are not returned to browser code. Preview is limited to Markdown document text.

## Gmail

Current GMAIL-MU1 connection endpoints:

- `POST /api/gmail/connect`
- `GET /api/gmail/status`
- `GET /api/gmail/callback`
- `POST /api/gmail/disconnect`

`connect`, `status`, and `disconnect` require the Neon Auth Bearer identity. The callback validates signed OAuth state before storing encrypted Google credentials for the mapped backend app user. The browser receives safe status metadata only, never Gmail tokens or OAuth client secrets.

Current GMAIL-MU2 manual fetch endpoint:

- `POST /api/gmail/fetch`

The manual fetch endpoint uses the mapped app user, connected encrypted Gmail credentials, backend source queries, existing email parsers, dedupe, relevance filters, and ingestion batch persistence. It returns a safe run summary only. The status shape supports connected/not-connected/token-expired/fetch-failed states, connected email display, last fetch metadata, detected sources, and `gmail.readonly` scope copy.

## Analysis

Manual Codex endpoints currently exist:

- `POST /api/analysis-requests`
- `POST /api/analysis-import`

Manual import remains the fallback. Browser requests return safe batch/file metadata and import counts; Codex itself remains outside the browser.

Current AI1 Gemini endpoint:

- `POST /api/analysis/run`

Future analysis batch endpoint:

- `GET /api/analysis/batches`

`POST /api/analysis/run` is backend-only orchestration. It requires the Neon Auth Bearer identity and accepts selected job ids. AI1 validates ownership, uses compact auth-scoped preferences and active DOC2 profile Markdown when available, calls Gemini, validates strict JSON, and persists provider-tagged analysis rows. The browser never receives `GEMINI_API_KEY`.

## Security Contract

- Backend returns safe configuration errors when required server configuration is missing.
- Split frontend/API deployments must configure explicit backend `API_CORS_ALLOWED_ORIGINS`; browser auth tokens do not justify wildcard origins.
- Auth-backed phases must enforce user data isolation on every owned resource.
- Raw Gmail bodies are not a Gemini analysis payload.
- Resume PDFs are not sent to Gemini by default.
