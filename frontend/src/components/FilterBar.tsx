import type { JobStatus, Priority, Source } from "../types";

export interface JobFilters {
  status: JobStatus | "all";
  source: Source | "all";
  priority: Priority | "all";
  location: string;
  likelyRelevantOnly: boolean;
  search: string;
}

export default function FilterBar({
  filters,
  onChange,
}: {
  filters: JobFilters;
  onChange: (filters: JobFilters) => void;
}) {
  return (
    <div className="flex shrink-0 flex-wrap items-center gap-3 border-b border-surface-variant bg-surface-bright p-4">
      <div className="relative w-full md:w-64">
        <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-on-surface-variant">
          search
        </span>
        <input
          className="w-full rounded-md border border-outline-variant bg-surface-container-low py-1.5 pl-9 pr-3 font-body-md text-body-md outline-none transition-all focus:border-primary focus:ring-1 focus:ring-primary"
          onChange={(event) => onChange({ ...filters, search: event.target.value })}
          placeholder="Search jobs..."
          type="text"
          value={filters.search}
        />
      </div>
      <select
        className="rounded-md border border-outline-variant bg-surface-container-low px-3 py-1.5 pr-8 font-body-md text-body-md text-primary outline-none focus:border-primary focus:ring-1 focus:ring-primary"
        onChange={(event) => onChange({ ...filters, source: event.target.value as JobFilters["source"] })}
        value={filters.source}
      >
        <option value="all">Source: All</option>
        <option value="LinkedIn">LinkedIn</option>
        <option value="StepStone">StepStone</option>
        <option value="Indeed">Indeed</option>
      </select>
      <select
        className="rounded-md border border-outline-variant bg-surface-container-low px-3 py-1.5 pr-8 font-body-md text-body-md text-primary outline-none focus:border-primary focus:ring-1 focus:ring-primary"
        onChange={(event) => onChange({ ...filters, priority: event.target.value as JobFilters["priority"] })}
        value={filters.priority}
      >
        <option value="all">Codex Priority: All</option>
        <option value="High">High</option>
        <option value="Medium">Medium</option>
        <option value="Low">Low</option>
        <option value="Not analyzed">Not analyzed</option>
      </select>
      <select
        className="rounded-md border border-outline-variant bg-surface-container-low px-3 py-1.5 pr-8 font-body-md text-body-md text-primary outline-none focus:border-primary focus:ring-1 focus:ring-primary"
        onChange={(event) => onChange({ ...filters, location: event.target.value })}
        value={filters.location}
      >
        <option value="all">Location: All</option>
        <option value="Berlin">Berlin</option>
        <option value="Potsdam">Potsdam</option>
        <option value="Remote">Remote</option>
        <option value="Hybrid">Hybrid</option>
      </select>
      <label className="ml-auto flex cursor-pointer items-center gap-2 font-body-md text-body-md text-primary">
        <input
          checked={filters.likelyRelevantOnly}
          className="h-4 w-4 rounded border-outline-variant text-primary focus:ring-primary"
          onChange={(event) => onChange({ ...filters, likelyRelevantOnly: event.target.checked })}
          type="checkbox"
        />
        Likely Relevant Only
      </label>
    </div>
  );
}
