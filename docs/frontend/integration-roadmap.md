# Frontend Integration Roadmap

## F1 Static Mock Dashboard

- React/Vite/TypeScript/Tailwind app.
- Mock users, jobs, runs, preferences, and documents.
- Local state for status changes and modals.
- No backend API calls.

## F2 API Contract And Local API Server

- Add local API under `api/`.
- Implement read-only routes against Neon.
- Keep frontend client switchable between mock and real clients.

## F3 Read-Only Real Data Connection

- Connect overview/jobs/settings to the API.
- Keep status updates disabled until F4.

## F4 Status Update Integration

- Wire save/applied/ignored actions to `PATCH /api/user-jobs/{job_id}/status`.
- Preserve status vs discovery distinction.

## F5 Prepare Codex Analysis Integration

- Wire Prepare Codex Analysis modal to the API/CLI service.
- Return generated file paths.
- Still no AI API calls.

## F6 Import Analysis Result Integration

- Wire import modal to select a local structured JSON result path.
- Store analyses in Neon.

## F7 Post-Import Refresh

- Refresh jobs, overview, and latest analysis data after import.
- Keep manual Refresh Data available for local API mode.
- Show latest score/priority/reason/concern from API data.

## F8 Profile/Resume Upload Integration

- Add local document upload handling.
- Store files under `private/`.
- Store only metadata and paths in Neon.

## F9 Polish And Responsive Behavior

- Browser QA across desktop/mobile.
- Accessibility pass.
- Empty/error/loading states.
- Optional Docker Compose service for frontend dev server.
