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

## Current Phase

### AUTH0

- Document Neon Auth and Google login feasibility, frontend auth seam, identity mapping direction, and multi-user migration risks.
- Keep browser auth state mock-only while onboarding route behavior is refined.
- Do not implement real OAuth, backend session validation, Gmail OAuth, or Gemini runtime analysis.

## Next UI And Auth Phases

### ONBOARD1

- Extend onboarding UI state and setup checklist around preferences, Gmail connection, and documents.

### AUTH1

- Add Neon Auth Google login frontend foundation.

### AUTH2

- Validate backend sessions and expose authenticated identity through `/api/me`.

### AUTH3

- Move fixed development user ids toward auth-backed user profiles and ownership enforcement.

## Analysis And Gmail Phases

### AI1

- Implement backend-only Gemini analysis service, strict JSON validation, provider-aware storage, and safe limits.

### AI2

- Wire Jobs UI `Run Gemini Analysis` to backend analysis endpoint and refresh dashboard data.

### GMAIL-MU1

- Add per-user Gmail OAuth connection and status handling.

### GMAIL-MU2

- Add per-user Gmail fetch and job ingestion path.

## Documents And Deployment

### DOC2

- Harden auth-scoped document access, preview, lifecycle, and private path safety.

### DEPLOY1

- Plan deployment boundaries for frontend, API, Neon, OAuth redirects, secret storage, and operations.

## Ongoing Polish

- Responsive and accessibility checks.
- Empty/loading/error states.
- Docker/dev workflow upkeep.
- Security review before any public deployment.
