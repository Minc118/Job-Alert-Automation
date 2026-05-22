# Frontend And Web App Roadmap

## Completed Foundation

### F1 Static Mock Dashboard

- React/Vite/TypeScript/Tailwind dashboard shell.
- Overview, jobs, settings, drawer, filters, and mock data.

### F2 API Contract And Local API Server

- FastAPI dashboard boundary.
- Initial read endpoints over backend services.

### F3 Read-Only Real Data Connection

- Frontend mock/real API mode switch.
- Overview, jobs, runs, settings, and drawer reads.

### F4 Status Update Integration

- Save/applied/ignored actions through backend status endpoint.
- Status remains separate from discovery.

### F5 Prepare Codex Analysis Integration

- Manual request preparation through backend services.

### F6 Import Analysis Result Integration

- Structured manual Codex import path through backend services.

### F7 Profile/Resume Foundation

- Profile/resume UI and document architecture foundation added before auth hardening.
- Auth-scoped backend document hardening remains staged for DOC2.

### UI-PUBLIC1 Public Routes And Mock Auth

- Archive Stitch landing reference.
- Add landing and Google-only login pages.
- Add React Router, guarded `/app/*`, mock onboarding, and mock-only `/demo/*`.
- Keep Google app login separate from Gmail OAuth in all copy.
- Do not add real auth or backend runtime changes yet.

### REFACTOR1 Backend Directory Move

- Move Python package, API, tests, migrations, config, and backend build files into `backend/`.
- Keep CLI, FastAPI, Docker, and frontend runtime behavior unchanged.

### AUTH0

- Document Neon Auth and Google login feasibility, frontend auth seam, identity mapping direction, and multi-user migration risks.
- Keep browser auth state mock-only while onboarding route behavior is refined.
- Do not implement real OAuth, backend session validation, Gmail OAuth, or Gemini runtime analysis.

### AUTH1

- Add Neon Auth Google login frontend foundation behind the existing auth seam.
- Keep mock auth as the default/fallback local mode.
- Keep backend session validation, Gmail OAuth, and Gemini runtime analysis staged.

### AUTH2

- Validate Neon Auth JWTs in FastAPI and expose authenticated identity through `/api/me`.
- Keep dashboard ownership mapping staged so fixed development users are not exposed as Google-account data.

### GMAIL-MU2

- Add per-user manual Gmail fetch and job ingestion path.
- Reuse existing parser/dedupe/filter/batch persistence from the backend CLI without a scheduler.

### AI1

- Add backend-only Gemini analysis endpoint with ownership validation, strict structured result validation, safe per-run limits, and provider-tagged analysis storage.

### AI2

- Wire authenticated Jobs selection to `Run Gemini Analysis`.
- Refresh jobs after the backend stores Gemini results.

### DOC2

- Add auth-scoped profile/resume metadata, private upload storage, activate/delete lifecycle, and Markdown preview.
- Prefer active profile Markdown as Gemini matching context while keeping resume PDFs out of Gemini by default.

### AUTH3

- Map Neon Auth subjects to backend-owned app profiles without reusing fixed development users.
- Add session-scoped overview/jobs/runs reads and keep existing compatibility paths.

### ONBOARD1

- Persist auth-scoped job preferences and onboarding completion.
- Keep Gmail connection and document upload steps staged.

### GMAIL-MU1

- Add per-user Gmail readonly OAuth connect/status/disconnect handling.
- Store Google credentials encrypted behind FastAPI and mapped app-user ownership.
- Keep per-user fetch and ingestion out of this phase.

## Current Phase

### DEPLOY1

- Document deployment boundaries for frontend, API, Neon, OAuth redirects, secret storage, runtime private storage, and operations.
- Add explicit FastAPI CORS origin configuration for split frontend/API deployments while keeping local defaults.

## Next Deployment Work

- Choose the actual frontend/API hosting topology.
- Decide durable private document storage and backup/retention policy before multi-instance document serving.
- Add release automation only after secrets, OAuth callback URLs, and migration workflow are fixed for the chosen target.

## Ongoing Polish

- Responsive and accessibility checks.
- Empty/loading/error states.
- Docker/dev workflow upkeep.
- Security review before any public deployment.
