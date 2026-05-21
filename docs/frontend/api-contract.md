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
- `GET /api/overview?user_id=minjian&range=latest_run`
- `GET /api/jobs?user_id=minjian&range=latest_run`
- `GET /api/jobs/{job_id}?user_id=minjian`
- `GET /api/runs?user_id=minjian`
- `PATCH /api/user-jobs/{job_id}/status`
- `POST /api/analysis-requests`
- `POST /api/analysis-import`

UI-PUBLIC1 and AUTH0 do not add backend runtime endpoints. AUTH0 documents the identity/session boundary for later phases.

## Session And Auth Direction

Future:

`GET /api/me`

Returns session-backed identity, onboarding readiness, and safe display metadata for the authenticated browser user. The first useful shape is:

```json
{
  "authenticated": true,
  "user": {
    "id": "auth-backed-app-user-id",
    "display_name": "Minjian"
  },
  "onboarding": {
    "complete": false,
    "missing_steps": ["preferences", "gmail_connection"]
  }
}
```

Google app login and Gmail OAuth are separate. Session routes must not imply mailbox authorization.

Once backend sessions exist, owned-resource endpoints should prefer session-derived ownership over trusting browser-provided `user_id` query parameters.

## Users And Preferences

Current:

`GET /api/users`

Future:

- `GET /api/user/preferences`
- `PATCH /api/user/preferences`

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

- `GET /api/users/{user_id}/documents`
- `POST /api/users/{user_id}/documents`
- `PATCH /api/users/{user_id}/documents/{document_id}/activate`
- `DELETE /api/users/{user_id}/documents/{document_id}`

Document APIs are a staged direction after the current profile/resume UI foundation. They must expose safe metadata and authorized operations without exposing `private/` as a public filesystem.

## Gmail Direction

Future:

- `POST /api/gmail/connect`
- `GET /api/gmail/status`
- `POST /api/gmail/fetch`

The status shape should support connected/not-connected/token-expired/fetch-failed states, connected email display, last fetch metadata, detected sources, and `gmail.readonly` scope copy.

## Analysis

Manual Codex endpoints currently exist:

- `POST /api/analysis-requests`
- `POST /api/analysis-import`

Manual import remains the fallback. Browser requests return safe batch/file metadata and import counts; Codex itself remains outside the browser.

Future Gemini endpoints:

- `POST /api/analysis/run`
- `GET /api/analysis/batches`

`POST /api/analysis/run` is backend-only orchestration. The frontend sends selected job ids; backend validates ownership, loads compact active profile summary data, calls Gemini, validates strict JSON, and persists provider-tagged analysis rows. The browser never receives `GEMINI_API_KEY`.

## Security Contract

- Backend returns safe configuration errors when required server configuration is missing.
- Auth-backed phases must enforce user data isolation on every owned resource.
- Raw Gmail bodies are not a Gemini analysis payload.
- Resume PDFs are not sent to Gemini by default.
