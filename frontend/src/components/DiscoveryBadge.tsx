import type { Discovery } from "../types";

const discoveryLabels: Record<Discovery, string> = {
  new_in_this_run: "New in this run",
  seen_before: "Seen before",
  historical: "Historical",
};

export function getDiscoveryLabel(discovery: Discovery): string {
  return discoveryLabels[discovery];
}

export default function DiscoveryBadge({ discovery }: { discovery: Discovery }) {
  const classes =
    discovery === "new_in_this_run"
      ? "bg-secondary-container text-on-secondary-fixed"
      : discovery === "seen_before"
        ? "bg-surface-container-highest text-on-surface-variant"
        : "bg-surface text-outline border border-surface-variant";

  return (
    <span className={`inline-flex items-center rounded px-2 py-0.5 text-[10px] font-bold ${classes}`}>
      {discoveryLabels[discovery]}
    </span>
  );
}
