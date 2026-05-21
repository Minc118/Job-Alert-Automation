import type { Job, OverviewData, Source } from "../types";

const sourceColors = {
  LinkedIn: "bg-primary",
  StepStone: "bg-secondary",
  Indeed: "bg-outline",
};

export default function SourceSummary({ jobs, counts }: { jobs: Job[]; counts?: OverviewData["sourceSummary"] }) {
  const derivedCounts = ["LinkedIn", "StepStone", "Indeed"].map((source) => ({
    source,
    count: counts?.[source as Source] ?? jobs.filter((job) => job.source === source).length,
  }));
  const total = Math.max(derivedCounts.reduce((sum, item) => sum + item.count, 0), 1);

  return (
    <section className="rounded-xl bg-surface-container-lowest p-6 shadow-ambient">
      <h3 className="mb-6 font-headline-sm text-headline-sm text-primary">Source Summary</h3>
      <div className="space-y-5">
        {derivedCounts.map(({ source, count }) => (
          <div key={source}>
            <div className="mb-1 flex justify-between">
              <span className="font-label-md text-label-md text-on-surface">{source}</span>
              <span className="font-label-md text-label-md text-primary">{count}</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-surface-variant">
              <div
                className={`h-1.5 rounded-full ${sourceColors[source as keyof typeof sourceColors]}`}
                style={{ width: `${Math.round((count / total) * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
