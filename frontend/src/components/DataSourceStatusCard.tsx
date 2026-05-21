import type { DataSourceStatus } from "../types";

export default function DataSourceStatusCard({ source }: { source: DataSourceStatus }) {
  const active = source.status === "active";

  return (
    <div className="flex items-center justify-between border-b border-surface-variant bg-surface p-4 last:border-b-0 hover:bg-surface-container-low">
      <div className="flex flex-col">
        <span className={`font-body-md text-body-md font-medium text-on-surface ${active ? "" : "opacity-70"}`}>{source.source}</span>
        <span className="font-label-sm text-label-sm text-on-surface-variant">
          {active ? `Active, last seen ${source.lastSeenAt}` : "Disconnected"}
        </span>
      </div>
      <div className={`relative h-4 w-8 rounded-full ${active ? "bg-primary-container" : "bg-surface-variant"}`}>
        <div className={`absolute top-0.5 h-3 w-3 rounded-full ${active ? "right-1 bg-on-primary" : "left-1 bg-on-surface-variant"}`} />
      </div>
    </div>
  );
}
