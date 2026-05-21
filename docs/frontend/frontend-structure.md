# Frontend Structure

## Route Groups

Public routes:

- `/`: `PublicLandingPage`
- `/login`: `LoginPage`
- `/demo/*`: mock-only `DashboardApp`

Mock-gated app routes:

- `/onboarding`: `OnboardingFlow`
- `/app`: redirect to `/app/overview`
- `/app/overview`: dashboard overview
- `/app/jobs`: jobs workspace
- `/app/settings`: settings workspace

AUTH0 uses `AuthProvider`, `AuthGate`, and versioned `sessionStorage` mock auth/onboarding state. Real authentication and backend session validation are deferred.

## Pages

- `PublicLandingPage`: landing hero, product preview, how-it-works, privacy, demo CTA.
- `LoginPage`: Google-only mock sign-in entry.
- `OnboardingFlow`: mock welcome, preferences, Gmail connection, profile/resume, finish steps.
- `OverviewPage`: metrics, latest run summary, source summary, top recommendations, recent activity.
- `JobsPage`: status tabs, filters, job table, analysis actions, right-side job detail drawer.
- `SettingsPage`: preferences, Gmail Connection panel, profile/resume documents, data sources, system notes.

## Shared Layout

- Router root in `App`
- `DashboardApp` for `/app/*` and `/demo/*`
- `AuthProvider` and `useAuth` seam for the current mock session model and future auth providers
- `AuthGate`
- `AppShell`
- `Sidebar`
- `Topbar`
- Mobile topbar and bottom navigation
- Drawer and modal primitives

Demo mode must always select mock clients and data. App mode may use configured mock or real API clients.

## Shared Components

- `MetricCard`
- `LatestRunSummary`
- `SourceSummary`
- `RecentActivity`
- `TopRecommendedJobs`
- `JobTable`
- `JobRow`
- `JobDetailDrawer`
- `CodexAnalysisPanel`
- `GPTApplicationPromptBox`
- `StatusBadge`
- `DiscoveryBadge`
- `PriorityBadge`
- `FilterBar`
- `SettingsSection`
- `GmailConnectionPanel`
- `ProfileResumeSection`
- `PrivateProfileFileStatus`
- `DataSourceStatusCard`
- `SystemNotesCard`
- `PrepareAnalysisModal`
- `ImportAnalysisModal`

## Data Models

Frontend models include:

- `User`
- `Job`
- `CodexJobAnalysis`
- `IngestionRun`
- `UserPreferences`
- `UserDocument`
- `DataSourceStatus`

AUTH0 auth models include safe mock session state and onboarding progress. Future auth-backed models add backend session identity, Gmail connection state, and Gemini analysis batch metadata without exposing secrets.

## Backend Data Requirements

The backend boundary must provide:

- Overview counters and latest run summaries.
- Jobs with status, discovery, rule matches, latest analysis, and link metadata.
- User preferences and source summaries.
- Backend-mediated document metadata and actions.
- Status and manual Codex prepare/import actions already staged.
- Later auth, Gmail connection, and backend-only Gemini actions.

## UX Corrections

- Keep status and discovery separate in table and copy.
- Do not imply browser-side Neon, Gmail token, or Gemini access.
- Distinguish Google login from Gmail readonly connection.
- Keep demo data public and mock-only.
- Keep Berlin, Potsdam, Remote, Hybrid Berlin, and Hybrid Potsdam examples.
