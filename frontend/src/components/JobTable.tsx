import type { Job, JobStatus } from "../types";
import JobRow from "./JobRow";

export default function JobTable({
  jobs,
  selectedJobId,
  selectedJobIds,
  onSelectJob,
  onSelectionChange,
  onStatusChange,
}: {
  jobs: Job[];
  selectedJobId: number | null;
  selectedJobIds: number[];
  onSelectJob: (job: Job) => void;
  onSelectionChange: (jobIds: number[]) => void;
  onStatusChange: (jobId: number, status: JobStatus) => void | Promise<void>;
}) {
  const visibleJobIds = jobs.map((job) => job.id);
  const selectedVisibleJobIds = visibleJobIds.filter((jobId) => selectedJobIds.includes(jobId));
  const allVisibleSelected = visibleJobIds.length > 0 && selectedVisibleJobIds.length === visibleJobIds.length;

  function toggleVisibleJobs(checked: boolean) {
    if (!checked) {
      onSelectionChange(selectedJobIds.filter((jobId) => !visibleJobIds.includes(jobId)));
      return;
    }
    onSelectionChange([...new Set([...selectedJobIds, ...visibleJobIds])]);
  }

  return (
    <div className="flex-1 overflow-auto bg-surface-container-lowest">
      <table className="w-full border-collapse text-left">
        <thead className="sticky top-0 z-10 border-b border-surface-variant bg-surface-container-low shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
          <tr>
            <th className="w-10 p-3">
              <input
                aria-label="Select visible jobs"
                checked={allVisibleSelected}
                className="h-4 w-4 rounded border-outline-variant text-primary focus:ring-primary"
                onChange={(event) => toggleVisibleJobs(event.currentTarget.checked)}
                type="checkbox"
              />
            </th>
            <th className="p-3 font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Discovery</th>
            <th className="p-3 font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Title & Company</th>
            <th className="p-3 font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Location</th>
            <th className="p-3 font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Codex</th>
            <th className="p-3 font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Status</th>
            <th className="p-3 text-right font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-surface-variant font-body-md text-body-md">
          {jobs.map((job) => (
            <JobRow
              job={job}
              checked={selectedJobIds.includes(job.id)}
              key={job.id}
              onCheckedChange={(jobId, checked) =>
                onSelectionChange(checked ? [...new Set([...selectedJobIds, jobId])] : selectedJobIds.filter((id) => id !== jobId))
              }
              onSelect={() => onSelectJob(job)}
              onStatusChange={onStatusChange}
              selected={selectedJobId === job.id}
            />
          ))}
        </tbody>
      </table>
      {jobs.length === 0 ? (
        <div className="p-8 text-center font-body-md text-body-md text-on-surface-variant">No jobs match the current filters.</div>
      ) : null}
    </div>
  );
}
