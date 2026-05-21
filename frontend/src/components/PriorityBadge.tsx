import type { Priority } from "../types";

export default function PriorityBadge({ priority }: { priority: Priority }) {
  const classes: Record<Priority, string> = {
    High: "bg-secondary-fixed text-on-secondary-fixed",
    Medium: "bg-surface-container-high text-on-surface",
    Low: "bg-surface-container text-on-surface-variant",
    "Not analyzed": "bg-surface text-outline border border-surface-variant",
  };

  return <span className={`rounded px-2 py-0.5 text-label-sm font-label-sm ${classes[priority]}`}>{priority}</span>;
}
