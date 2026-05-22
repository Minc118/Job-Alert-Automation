# DEPLOY1 Deployment Plan

DEPLOY1 documents the deployment boundary. It does not deploy the app, add a cloud vendor lock-in, or change product behavior.

## Target Topology

The production data path remains:

```text
Browser
  -> static React frontend
  -> FastAPI backend
  -> Neon PostgreSQL
```

The frontend can be hosted as static Vite build output. FastAPI must run in a backend runtime that can hold backend-only environment variables, reach Neon, complete Google Gmail OAuth callbacks, and persist private document files until a dedicated document storage design replaces the current private filesystem path.

Public demo routes stay mock-only. Authenticated dashboard routes use Neon Auth session tokens and FastAPI ownership checks.

## Environment Layers

Only frontend-safe values may be compiled into the Vite build:

| Frontend variable | Purpose |
| --- | --- |
| `VITE_API_MODE` | `real` for a deployed API-backed app. |
| `VITE_API_BASE_URL` | Public FastAPI origin. |
| `VITE_AUTH_MODE` | `neon` when Google app login is enabled. |
| `VITE_NEON_AUTH_URL` | Public Neon Auth client URL. |

Backend-only settings must stay in the API runtime secret store or local root `.env`:

| Backend setting | Purpose |
| --- | --- |
| `DATABASE_URL` | Neon connection string for backend persistence only. |
| `NEON_AUTH_JWKS_URL` | JWT verification keys for FastAPI. |
| `GEMINI_API_KEY` | Backend Gemini analysis credential. |
| `GOOGLE_OAUTH_CLIENT_SECRETS_FILE` | Gmail OAuth client configuration path. |
| `GMAIL_OAUTH_STATE_SECRET` | Signs Gmail OAuth state. |
| `GMAIL_TOKEN_ENCRYPTION_KEY` | Encrypts per-user Gmail credentials at rest. |
| `GMAIL_OAUTH_REDIRECT_URI` | Backend Gmail OAuth callback URL. |
| `FRONTEND_BASE_URL` | Safe post-Gmail redirect target. |
| `API_CORS_ALLOWED_ORIGINS` | Explicit browser origins allowed to call FastAPI. |

Do not prefix secrets with `VITE_`. Vite bundles frontend-prefixed variables into browser code.

## Auth And OAuth Redirects

Application login and Gmail mailbox access are separate:

- Neon Auth Google login identifies the app user.
- Gmail OAuth uses a separate readonly grant for job alert email access.
- The Gmail OAuth callback must point at the deployed FastAPI callback route, not the frontend router.
- Google OAuth configuration must include the exact callback URL used by `GMAIL_OAUTH_REDIRECT_URI`.

For a deployed split-origin frontend/API pair, configure `API_CORS_ALLOWED_ORIGINS` with the frontend origin. Keep it as an explicit comma-separated allowlist so browser Bearer requests are permitted only from expected frontend origins.

## Neon And Migrations

FastAPI remains the only browser-facing database boundary. The frontend must not receive `DATABASE_URL` or connect directly to Neon.

Before deploying a backend revision that depends on new tables or columns:

1. Back up or branch the target Neon environment as appropriate for the release.
2. Apply migrations from the backend runtime or a controlled release job.
3. Verify `/api/health` and an authenticated `/api/me` request before enabling user-facing workflows.

Use separate Neon branches or projects for development/test and production data. Do not reuse local fixed-user data as authenticated production ownership data.

## Private Documents And Runtime Storage

DOC2 stores uploaded profile Markdown and resume PDFs under backend-private storage and persists safe metadata in Neon.

- The frontend receives metadata and Markdown preview content only.
- Resume PDF bytes and stored filesystem paths are not browser responses.
- A production backend must mount durable private storage for the current file-backed implementation.
- A later storage phase should define backup, retention, deletion, malware scanning, and multi-instance access before scaling document handling beyond a single durable backend storage boundary.

## Deployment Checklist

1. Build the frontend with only public `VITE_*` values.
2. Run backend tests and frontend build before release.
3. Configure backend secrets outside source control.
4. Set `API_CORS_ALLOWED_ORIGINS` to the deployed frontend origin list.
5. Set Neon Auth frontend URL and FastAPI JWKS URL for the same auth project.
6. Register the exact Gmail OAuth callback URL and set `FRONTEND_BASE_URL`.
7. Apply pending backend migrations.
8. Smoke test health, login, onboarding, Gmail connect/status, one manual fetch, one Gemini analysis selection, and document upload/delete on non-sensitive test data.
9. Monitor backend errors for database connectivity, JWKS fetch failures, Gmail token refresh failures, Gemini validation failures, and private storage failures.

## Not In DEPLOY1

- No production deployment automation is added here.
- No public domain, reverse proxy, or hosted storage provider is chosen here.
- No background Gmail schedule or queue is added here.
- No secret values are committed to the repository.
