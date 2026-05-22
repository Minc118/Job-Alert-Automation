import type { Job, JobStatus } from "../types";
import DiscoveryBadge from "./DiscoveryBadge";
import StatusBadge from "./StatusBadge";

function priorityDot(priority?: string) {
  if (priority === "High") return "bg-[#10b981]";
  if (priority === "Medium") return "bg-[#f59e0b]";
  if (priority === "Low") return "bg-[#ef4444]";
  return "bg-outline";
}

export default function JobRow({
  job,
  selected,
  checked,
  onSelect,
  onCheckedChange,
  onStatusChange,
}: {
  job: Job;
  selected: boolean;
  checked: boolean;
  onSelect: () => void;
  onCheckedChange: (jobId: number, checked: boolean) => void;
  onStatusChange: (jobId: number, status: JobStatus) => void | Promise<void>;
}) {
  const priority = job.codexAnalysis?.priority ?? "Not analyzed";
  const score = job.codexAnalysis?.score == null ? null : Math.round(job.codexAnalysis.score * 10);

  function openLink() {
    window.open(job.url, "_blank", "noopener,noreferrer");
  }

  return (
    <tr
      className={`cursor-pointer transition-colors hover:bg-surface-container-low ${
        selected ? "bg-surface-container" : ""
      } ${job.status === "ignored" ? "opacity-70" : ""}`}
      onClick={onSelect}
    >
      <td className="p-3">
        <input
          aria-label={`Select ${job.title}`}
          checked={checked}
          className="h-4 w-4 rounded border-outline-variant text-primary focus:ring-primary"
          onChange={(event) => onCheckedChange(job.id, event.currentTarget.checked)}
          onClick={(event) => event.stopPropagation()}
          type="checkbox"
        />
      </td>
      <td className="p-3">
        <DiscoveryBadge discovery={job.discovery} />
      </td>
      <td className="p-3">
        <div className={`font-semibold text-primary ${job.status === "ignored" ? "line-through" : ""}`}>{job.title}</div>
        <div className="mt-0.5 flex flex-wrap items-center gap-1 text-sm text-on-surface-variant">
          <span className="material-symbols-outlined text-[14px]">business</span>
          {job.company}
          <span className="mx-1">•</span>
          <span className="material-symbols-outlined text-[14px]">link</span>
          {job.source}
        </div>
      </td>
      <td className="p-3 text-on-surface-variant">{job.location}</td>
      <td className="p-3">
        <div className="flex items-center gap-2">
          <div className={`h-2 w-2 rounded-full ${priorityDot(priority)}`} />
          <span className="font-label-sm text-label-sm">
            {priority === "Not analyzed" ? "Not analyzed" : `${priority} • ${score}/100`}
          </span>
        </div>
      </td>
      <td className="p-3">
        <StatusBadge status={job.status} />
      </td>
      <td className="p-3 text-right">
        <div className="flex justify-end gap-1 text-on-surface-variant">
          <button
            className="rounded p-1.5 transition-colors hover:bg-surface-variant"
            onClick={(event) => {
              event.stopPropagation();
              openLink();
            }}
            title="Open Link"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">open_in_new</span>
          </button>
          <button
            className={`rounded p-1.5 transition-colors hover:bg-surface-variant ${job.status === "saved" ? "text-primary" : ""}`}
            onClick={(event) => {
              event.stopPropagation();
              onStatusChange(job.id, "saved");
            }}
            title="Save"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">{job.status === "saved" ? "bookmark" : "bookmark_border"}</span>
          </button>
          <button
            className="rounded p-1.5 transition-colors hover:bg-surface-variant"
            onClick={(event) => {
              event.stopPropagation();
              onStatusChange(job.id, "applied");
            }}
            title="Mark Applied"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">check_circle</span>
          </button>
        </div>
      </td>
    </tr>
  );
}
