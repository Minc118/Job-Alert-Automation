# AUTH0 Authentication Architecture

AUTH0 is a design and frontend-structure phase. It keeps the current dashboard usable while defining the boundary for real Neon Auth and Google login work later.

## Scope

AUTH0 includes:

- A documented public/login/onboarding route model.
- A frontend auth seam that is backed by mock session state today.
- Neon Auth and backend session validation direction for later phases.
- Separation of app authentication from Gmail mailbox authorization.

AUTH0 does not include:

- Real Neon Auth setup.
- Google OAuth callbacks.
- Backend `/api/me` runtime implementation.
- Gmail OAuth connection.
- Gemini runtime analysis.
- Auth migrations or destructive data changes.

## Route And Session Model

Current frontend routes are:

```text
/                  Public landing page
/login             Google-only login page
/onboarding        Mock setup flow
/app/*             Mock-gated dashboard
/demo/*            Public mock dashboard preview
```

Current browser state is intentionally mock-only:

- `AuthProvider` exposes the route gate contract used by public and dashboard pages.
- Session state is stored as a versioned `sessionStorage` snapshot for the current browser session.
- The snapshot tracks mock authenticated state and onboarding progress only.
- `/demo/*` remains public and uses mock dashboard data even if dashboard API mode is real.

The provider name and storage format are not a security boundary. AUTH1 should replace the mock provider behavior with Neon Auth frontend state without making public pages or dashboard routes depend on Neon directly.

## Target Authentication Boundary

Preferred direction:

```text
React public/login UI
  -> Neon Auth Google login
  -> browser session state
  -> FastAPI session validation
  -> Neon app data scoped by backend identity mapping
```

Google login is for app identity. It must not grant Gmail access or imply mailbox consent.

Gmail is a separate workflow:

```text
Authenticated user
  -> explicit Connect Gmail action
  -> Gmail OAuth readonly consent
  -> backend-owned Gmail token storage
  -> per-user job alert fetch
```

## Identity Mapping Direction

Existing development data uses fixed `app_users.id` values such as `minjian` and `chang`. AUTH work must preserve those rows until an explicit additive migration maps auth-backed identities.

The later mapping layer needs to answer:

- Which Neon Auth subject owns an app profile.
- Which app user id scopes jobs, runs, analyses, documents, preferences, and Gmail connections.
- Which onboarding readiness flags belong to that auth-backed app profile.

A future additive profile/mapping table is preferable to reinterpreting existing text ids or trusting browser-provided `user_id` query parameters after backend sessions exist.

## Backend Session Direction

`GET /api/me` is the first target session endpoint. It should return only safe session metadata:

- authenticated app user id
- display name
- onboarding completion/readiness
- allowed frontend feature state

Backend endpoints that operate on owned data should move from caller-trusted `user_id` parameters toward session-derived identity as AUTH2 and AUTH3 land.

## Security Invariants

- Frontend never receives Neon connection strings, Gmail secrets/tokens, Gemini keys, or private document file paths intended only for backend storage.
- Backend validates session ownership before returning jobs, runs, analyses, documents, or preferences in auth-backed phases.
- Login copy always distinguishes app authentication from Gmail readonly authorization.
- Real auth phases remain additive and preserve current local/manual CLI workflows.
