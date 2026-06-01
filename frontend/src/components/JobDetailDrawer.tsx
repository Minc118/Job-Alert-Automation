import type { Job, JobStatus } from "../types";
import AiAnalysisPanel from "./AiAnalysisPanel";
import DiscoveryBadge, { getDiscoveryLabel } from "./DiscoveryBadge";
import GPTApplicationPromptBox from "./GPTApplicationPromptBox";

export default function JobDetailDrawer({
  job,
  onClose,
  onStatusChange,
}: {
  job: Job | null;
  onClose: () => void;
  onStatusChange: (jobId: number, status: JobStatus) => void | Promise<void>;
}) {
  if (!job) {
    return (
      <aside className="hidden w-96 shrink-0 items-center justify-center rounded-xl border border-surface-variant bg-surface-container-lowest text-on-surface-variant shadow-lg lg:flex">
        Select a job to inspect details.
      </aside>
    );
  }

  return (
    <aside className="hidden w-96 shrink-0 flex-col overflow-hidden rounded-xl border border-surface-variant bg-surface-container-lowest shadow-lg lg:flex">
      <div className="sticky top-0 z-10 border-b border-surface-variant bg-surface-bright p-4">
        <h3 className="pr-8 font-headline-sm text-headline-sm font-bold leading-tight text-primary">{job.title}</h3>
        <p className="mt-1 flex items-center gap-1 font-body-md text-body-md text-on-surface-variant">
          {job.company}
          <span className="mx-1">•</span>
          {job.location}
        </p>
        <button
          className="absolute right-3 top-3 rounded-full bg-surface-container-low p-1 text-on-surface-variant hover:text-primary"
          onClick={onClose}
          type="button"
        >
          <span className="material-symbols-outlined text-[20px]">close</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg border border-surface-variant bg-surface-container-low p-3">
              <div className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Source</div>
              <div className="mt-1 flex items-center gap-1 font-label-md text-label-md">
                <span className="material-symbols-outlined text-[16px]">link</span>
                {job.source}
              </div>
            </div>
            <div className="rounded-lg border border-surface-variant bg-surface-container-low p-3">
              <div className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Discovery</div>
              <div className="mt-1">
                <DiscoveryBadge discovery={job.discovery} />
              </div>
            </div>
            <div className="col-span-2 rounded-lg border border-surface-variant bg-surface-container-low p-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Rule Match</div>
                  <div className="mt-1 font-label-md text-label-md text-primary">
                    {job.likelyRelevant ? "Likely Relevant" : "Needs Review"}
                  </div>
                </div>
                <span className={`material-symbols-outlined ${job.likelyRelevant ? "text-[#10b981]" : "text-outline"}`}>
                  {job.likelyRelevant ? "check_circle" : "help"}
                </span>
              </div>
              <p className="mt-3 font-body-md text-body-md text-on-surface-variant">{job.shortDescription}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {job.matchedKeywords.map((keyword) => (
                  <span className="rounded bg-surface px-2 py-1 text-label-sm text-on-surface-variant" key={keyword}>
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <AiAnalysisPanel analysis={job.codexAnalysis} />
          <GPTApplicationPromptBox prompt={job.gptPrompt} />

          <div className="rounded-lg border border-surface-variant bg-surface-container-low p-3 font-body-md text-body-md text-on-surface-variant">
            First seen: {job.firstSeenAt}
            <br />
            Last seen: {job.lastSeenAt}
            <br />
            Discovery state: {getDiscoveryLabel(job.discovery)}
          </div>
        </div>
      </div>

      <div className="sticky bottom-0 flex gap-2 border-t border-surface-variant bg-surface-bright p-4">
        <button
          className="flex-1 rounded-lg border border-outline-variant bg-surface-container py-2 font-label-md text-label-md font-bold text-primary transition-colors hover:bg-surface-container-high"
          onClick={() => onStatusChange(job.id, "ignored")}
          type="button"
        >
          Ignore
        </button>
        <button
          className="flex-1 rounded-lg bg-primary-container py-2 font-label-md text-label-md font-bold text-on-primary transition-opacity hover:opacity-90"
          onClick={() => onStatusChange(job.id, "applied")}
          type="button"
        >
          Mark Applied
        </button>
      </div>
    </aside>
  );
}
