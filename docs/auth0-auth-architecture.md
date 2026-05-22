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
- Backend `/api/me` runtime implementation, which now lands separately in AUTH2.
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

## AUTH1 Frontend Foundation

AUTH1 now adds the first frontend implementation behind the AUTH0 seam:

- Default frontend auth mode remains `mock`.
- `VITE_AUTH_MODE=neon` plus public `VITE_NEON_AUTH_URL` enables Neon Auth Google sign-in.
- Landing and login Google actions start app authentication through Neon Auth in neon mode.
- Frontend onboarding progress remains session-only until backend `/api/me` and setup readiness are implemented.

AUTH1 alone is not backend trust. Current dashboard APIs still use the existing development-mode user selection until AUTH2/AUTH3 add server-side session validation and ownership mapping.

## AUTH2 Backend Identity Check

AUTH2 adds the first backend trust boundary:

- Frontend Neon Auth mode sends a Neon Auth JWT to FastAPI `/api/me`.
- FastAPI validates the token signature and expiry against backend-only `NEON_AUTH_JWKS_URL`.
- `/api/me` returns safe subject/display metadata and explicitly marks account data as not ready.
- Existing jobs, runs, analyses, documents, and preferences are not returned from fixed-user endpoints for the authenticated Google account until AUTH3 maps ownership.

## AUTH3 App Profile Mapping

AUTH3 adds an additive `app_user_profiles` mapping:

- `auth_subject` is the Neon Auth identity boundary.
- `user_id` points to a backend-owned `app_users` row used by jobs, runs, analyses, documents, and preferences.
- `/api/me` provisions an empty auth-backed app user/profile when a valid Neon Auth subject first reaches FastAPI.
- Authenticated overview/jobs/runs reads omit browser-supplied `user_id`; FastAPI derives the app user from the JWT subject.
- Fixed `minjian` and `chang` development paths remain available for current CLI and compatibility workflows.

ONBOARD1 uses that mapping for the first persisted setup state:

- authenticated `GET/PATCH /api/user/preferences`
- authenticated `POST /api/onboarding/complete`
- backend stored target roles, preferred locations, and excluded keywords
- backend stored onboarding completion on `app_user_profiles`

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

`GET /api/me` is the first implemented session endpoint. It returns only safe session metadata:

- authenticated app user id
- display name
- onboarding completion/readiness
- allowed frontend feature state

AUTH3 moves the first read endpoints toward session-derived ownership. Preferences, documents, Gmail connection, analysis orchestration, and broader mutation hardening continue in staged work.

## Security Invariants

- Frontend never receives Neon connection strings, Gmail secrets/tokens, Gemini keys, or private document file paths intended only for backend storage.
- Backend validates session ownership before returning jobs, runs, analyses, documents, or preferences in auth-backed phases.
- Login copy always distinguishes app authentication from Gmail readonly authorization.
- Real auth phases remain additive and preserve current local/manual CLI workflows.
