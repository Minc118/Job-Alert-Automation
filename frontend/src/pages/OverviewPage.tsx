import type { IngestionRun, Job, OverviewData, User } from "../types";
import MetricCard from "../components/MetricCard";
import RecentActivity from "../components/RecentActivity";
import SourceSummary from "../components/SourceSummary";
import TopRecommendedJobs from "../components/TopRecommendedJobs";

export default function OverviewPage({
  user,
  jobs,
  latestRun,
  overview,
  onViewJobs,
}: {
  user: User;
  jobs: Job[];
  latestRun?: IngestionRun;
  overview?: OverviewData | null;
  onViewJobs: () => void;
}) {
  const calculatedMetrics = {
    newJobs: jobs.filter((job) => job.status === "new").length,
    newlyDiscovered: jobs.filter((job) => job.discovery === "new_in_this_run").length,
    likelyRelevant: jobs.filter((job) => job.likelyRelevant).length,
    highPriority: jobs.filter((job) => job.codexAnalysis?.priority === "High").length,
    saved: jobs.filter((job) => job.status === "saved").length,
    applied: jobs.filter((job) => job.status === "applied").length,
    ignored: jobs.filter((job) => job.status === "ignored").length,
  };
  const metrics = overview
    ? {
        newJobs: overview.metrics.newJobs,
        newlyDiscovered: overview.metrics.newlyDiscovered,
        likelyRelevant: overview.metrics.likelyRelevant,
        highPriority: overview.metrics.codexHighPriority,
        saved: overview.metrics.saved,
        applied: overview.metrics.applied,
        ignored: overview.metrics.ignored,
      }
    : calculatedMetrics;
  const displayedRun = overview?.latestRun ?? latestRun;
  const recommendedJobs = overview?.topRecommendedJobs ?? jobs;

  return (
    <main className="flex-1 p-margin_mobile pb-24 md:p-margin_desktop">
      <div className="mb-xl flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <div className="mb-2 flex items-center gap-3">
            <h2 className="m-0 font-display-lg text-display-lg text-primary">Overview</h2>
            <span className="rounded-sm bg-primary-container px-2 py-0.5 font-label-sm text-label-sm uppercase tracking-wider text-on-primary">
              {user.displayName}
            </span>
          </div>
          <p className="font-body-md text-body-md text-on-surface-variant">
            Last synchronization: {displayedRun?.completedAt ?? "No run available"}
          </p>
        </div>
        <button className="flex items-center justify-center gap-2 rounded-lg border border-outline-variant bg-surface-container px-4 py-2 font-label-md text-label-md text-on-surface transition-colors hover:bg-surface-variant">
          <span className="material-symbols-outlined text-[18px]">download</span>
          Export
        </button>
      </div>

      <div className="mb-xl grid grid-cols-2 gap-gutter md:grid-cols-4 lg:grid-cols-7">
        <MetricCard label="New Jobs" value={metrics.newJobs} />
        <MetricCard accent label="Newly Discovered" value={metrics.newlyDiscovered} />
        <MetricCard label="Likely Relevant" value={metrics.likelyRelevant} />
        <MetricCard highlight label="Codex High Priority" value={metrics.highPriority} />
        <MetricCard label="Saved" value={metrics.saved} />
        <MetricCard label="Applied" value={metrics.applied} />
        <MetricCard label="Ignored" muted value={metrics.ignored} />
      </div>

      <div className="mb-xl grid grid-cols-1 gap-gutter lg:grid-cols-12">
        <div className="flex flex-col gap-gutter lg:col-span-4">
          <section className="rounded-xl bg-surface-container-lowest p-6 shadow-ambient">
            <div className="mb-6 flex items-center justify-between">
              <h3 className="font-headline-sm text-headline-sm text-primary">Latest Run Summary</h3>
              <span className="material-symbols-outlined text-outline">update</span>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-surface-variant pb-2">
                <span className="font-body-md text-body-md text-on-surface-variant">Timestamp</span>
                <span className="font-label-md text-label-md text-primary">{displayedRun?.startedAt ?? "n/a"}</span>
              </div>
              <div className="flex items-center justify-between border-b border-surface-variant pb-2">
                <span className="font-body-md text-body-md text-on-surface-variant">Target User</span>
                <span className="font-label-md text-label-md text-primary">{user.displayName}</span>
              </div>
              <div className="grid grid-cols-2 gap-4 pt-2">
                <RunStat label="Emails Scanned" value={displayedRun?.emailsFetched ?? 0} />
                <RunStat label="Total Jobs Found" value={displayedRun?.jobsParsed ?? 0} />
                <RunStat label="Seen Again" value={displayedRun?.seenAgain ?? 0} />
                <RunStat label="Duplicates" value={displayedRun?.duplicatesSkipped ?? 0} />
              </div>
              <div className="mt-4 flex items-center justify-between rounded-lg bg-surface-container p-3">
                <span className="font-body-md text-body-md text-on-surface">Codex Analyzed</span>
                <span className="font-headline-sm text-headline-sm text-primary">{displayedRun?.codexAnalyzed ?? 0}</span>
              </div>
            </div>
          </section>
          <SourceSummary counts={overview?.sourceSummary} jobs={jobs} />
          <RecentActivity items={overview?.recentActivity} />
        </div>
        <div className="lg:col-span-8">
          <TopRecommendedJobs jobs={recommendedJobs} onViewAll={onViewJobs} />
        </div>
      </div>
    </main>
  );
}

function RunStat({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <span className="mb-1 block font-label-sm text-label-sm text-on-surface-variant">{label}</span>
      <span className="font-body-lg text-body-lg font-semibold text-primary">{value}</span>
    </div>
  );
}
