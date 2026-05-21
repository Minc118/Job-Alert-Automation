# Future API Contract

F1 uses mock data only. These endpoints define the future local API contract and are not implemented in F1.

## Users

`GET /api/users`

Returns:

```json
[
  { "id": "minjian", "displayName": "Minjian" },
  { "id": "chang", "displayName": "Chang" }
]
```

## Overview

`GET /api/overview?user_id=minjian&range=latest_run`

Returns overview metrics, latest run summary, source summary, recent activity, and top recommended jobs.

## Jobs

`GET /api/jobs?user_id=minjian&range=latest_run&status=new`

Returns dashboard-safe jobs with:

- status
- discovery
- rule-based relevance
- latest Codex analysis
- source link
- batch/run metadata

`GET /api/jobs/{job_id}`

Returns one detailed job record.

`PATCH /api/user-jobs/{job_id}/status`

Body:

```json
{ "userId": "minjian", "status": "saved" }
```

Valid statuses: `new`, `saved`, `applied`, `ignored`.

Implemented in F4 for status only. It does not change discovery or ingestion batch data.

## Runs

`GET /api/runs?user_id=minjian`

Returns ingestion run summaries.

## Analysis

`POST /api/analysis-requests`

Prepares Markdown/JSON request files. Does not call any AI API.

Implemented in F5. The browser receives only metadata such as analysis batch id, job count, and generated local paths.

`POST /api/analysis-import`

Imports structured Codex JSON result into Neon. Implemented in F6.

Request:

```json
{
  "resultPath": "output/analysis_results/latest_minjian_result.json",
  "overwrite": false
}
```

The API only accepts JSON files inside `output/analysis_results`.

Response:

```json
{
  "importedCount": 3,
  "skippedCount": 0,
  "updatedStatusesCount": 2,
  "resultPath": "output/analysis_results/latest_minjian_result.json",
  "message": "Analysis result imported. No AI API was called."
}
```

## Documents

`GET /api/users/{user_id}/documents`

`POST /api/users/{user_id}/documents`

`PATCH /api/users/{user_id}/documents/{document_id}/activate`

`DELETE /api/users/{user_id}/documents/{document_id}`

Document endpoints expose metadata only, not direct private file URLs.

## Security

- Browser never receives `DATABASE_URL`.
- Browser never receives Gmail tokens or OAuth secrets.
- Browser never receives private profile/resume file contents unless explicitly rendered by a safe local API route later.
- No OpenAI, Gemini, Codex, or LLM API calls.
