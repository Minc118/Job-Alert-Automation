import type { Job } from "../types";
import DiscoveryBadge from "./DiscoveryBadge";
import PriorityBadge from "./PriorityBadge";
import StatusBadge from "./StatusBadge";

export default function TopRecommendedJobs({ jobs, onViewAll }: { jobs: Job[]; onViewAll: () => void }) {
  const recommended = jobs
    .filter((job) => job.codexAnalysis?.priority === "High" || job.codexAnalysis?.priority === "Medium")
    .sort((a, b) => (b.codexAnalysis?.score ?? 0) - (a.codexAnalysis?.score ?? 0))
    .slice(0, 3);

  return (
    <section>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-headline-sm text-headline-sm text-primary">Top Recommended Jobs</h3>
        <button className="font-label-md text-label-md text-secondary hover:underline" onClick={onViewAll} type="button">
          View All
        </button>
      </div>
      <div className="space-y-4">
        {recommended.map((job, index) => (
          <article
            className={`rounded-xl bg-surface-container-lowest p-5 shadow-ambient transition-all duration-200 hover:-translate-y-px hover:shadow-ambient-hover ${
              index === 0 ? "border-l-4 border-primary" : ""
            }`}
            key={job.id}
          >
            <div className="mb-3 flex items-start justify-between gap-4">
              <div>
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <PriorityBadge priority={job.codexAnalysis?.priority ?? "Not analyzed"} />
                  <DiscoveryBadge discovery={job.discovery} />
                </div>
                <h4 className="font-headline-sm text-headline-sm leading-tight text-primary">{job.title}</h4>
                <p className="mt-1 font-body-md text-body-md text-on-surface">{job.company}</p>
              </div>
              <div className="flex shrink-0 items-center gap-1 rounded bg-surface-container-low px-2 py-1">
                <span className="font-label-sm text-label-sm text-on-surface-variant">Codex Score</span>
                <span className="font-headline-sm text-headline-sm text-primary">
                  {job.codexAnalysis?.score == null ? "--" : Math.round(job.codexAnalysis.score * 10)}
                </span>
              </div>
            </div>
            <div className="mb-4 flex flex-wrap items-center gap-4 font-label-md text-label-md text-on-surface-variant">
              <span className="flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px]">location_on</span>
                {job.location}
              </span>
              <span className="flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px]">work</span>
                {job.source}
              </span>
            </div>
            <div className="mb-4 rounded-lg border border-surface-variant bg-surface p-3">
              <span className="mb-1 block font-label-sm text-label-sm uppercase tracking-wide text-secondary">Codex Reasoning</span>
              <p className="font-body-md text-body-md text-on-surface">{job.codexAnalysis?.reason ?? "Not analyzed yet."}</p>
            </div>
            <div className="flex items-center justify-between gap-3 pt-2">
              <StatusBadge status={job.status} />
              <button
                className="flex items-center gap-1 rounded-lg bg-primary-container px-4 py-1.5 font-label-md text-label-md text-on-primary transition-opacity hover:opacity-90"
                onClick={() => window.open(job.url, "_blank", "noopener,noreferrer")}
                type="button"
              >
                Open Link
                <span className="material-symbols-outlined text-[16px]">open_in_new</span>
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
