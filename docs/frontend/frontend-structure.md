# Frontend Structure

## Pages

- `OverviewPage`: metrics, latest run summary, source summary, top recommendations, recent activity.
- `JobsPage`: status tabs, filters, job table, action buttons, right-side job detail drawer.
- `SettingsPage`: preferences, Profile & Resume mock UI, data sources, system notes.

## Shared Layout

- `AppShell`: desktop sidebar, topbar, mobile bottom nav, main content region.
- `Sidebar`: Overview, Jobs, Settings, Run Fetch action.
- `Topbar`: refresh action, latest-run indicator, user selector.
- `MainContent`: page canvas with desktop/mobile responsive padding.
- `MobileTopbar`: compact page title and profile icon.
- `MobileBottomNav`: Overview/Jobs/Settings navigation.
- `RightSideDrawer`: used by job details.
- `Modal`: shared modal primitive.

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
- `ActionButton`
- `SettingsSection`
- `ProfileResumeSection`
- `PrivateProfileFileStatus`
- `DataSourceStatusCard`
- `SystemNotesCard`
- `PrepareAnalysisModal`
- `ImportAnalysisModal`

## Data Models

The F1 frontend defines TypeScript models:

- `User`
- `Job`
- `CodexJobAnalysis`
- `IngestionRun`
- `UserPreferences`
- `UserDocument`
- `DataSourceStatus`

## Backend Data Requirements

The future API must provide:

- Overview counters by user and selected range.
- Latest ingestion run summary.
- Source summary.
- Jobs with status, discovery, rule matches, and latest Codex analysis.
- User preferences.
- Document metadata for private profiles and resumes.
- Action endpoints for status updates and manual Codex prepare/import workflows.

## UX Corrections

- Keep status and discovery as separate table columns/badges.
- Avoid language implying browser-side AI calls.
- Keep upload controls disabled/mock-only in F1.
- Use Berlin, Potsdam, Remote, Hybrid Berlin, and Hybrid Potsdam examples.
- Keep dashboard density close to the Stitch table/card layout.
