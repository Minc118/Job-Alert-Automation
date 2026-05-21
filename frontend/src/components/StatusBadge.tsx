import type { JobStatus } from "../types";

const statusLabels: Record<JobStatus, string> = {
  new: "Unprocessed",
  saved: "Saved",
  applied: "Applied",
  ignored: "Ignored",
};

export function getStatusLabel(status: JobStatus): string {
  return statusLabels[status];
}

export default function StatusBadge({ status }: { status: JobStatus }) {
  const muted = status === "ignored";

  return (
    <span
      className={`inline-flex items-center rounded-full border border-surface-variant bg-surface px-2 py-1 text-xs font-medium ${
        muted ? "text-outline" : "text-on-surface-variant"
      }`}
    >
      {statusLabels[status]}
    </span>
  );
}
