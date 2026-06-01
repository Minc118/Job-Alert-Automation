import { useEffect, useMemo, useState } from "react";
import FilterBar, { type JobFilters } from "../components/FilterBar";
import ImportAnalysisModal from "../components/ImportAnalysisModal";
import JobDetailDrawer from "../components/JobDetailDrawer";
import JobTable from "../components/JobTable";
import PrepareAnalysisModal from "../components/PrepareAnalysisModal";
import type { AiAnalysisRunResult, AnalysisImportResult, AnalysisRequestResult, Job, JobStatus, User } from "../types";
import { getStatusLabel } from "../components/StatusBadge";

const tabs: Array<{ value: JobFilters["status"]; label: string }> = [
  { value: "all", label: "All" },
  { value: "new", label: "Unprocessed" },
  { value: "saved", label: "Saved" },
  { value: "applied", label: "Applied" },
  { value: "ignored", label: "Ignored" },
];

export default function JobsPage({
  user,
  jobs,
  loadJobDetail,
  onImportAnalysis,
  onPrepareAnalysis,
  onRefreshData,
  onRunAiAnalysis,
  onStatusChange,
  manualAnalysisEnabled = true,
  aiAnalysisEnabled = false,
}: {
  user: User;
  jobs: Job[];
  loadJobDetail: (jobId: number) => Promise<Job>;
  onImportAnalysis: (resultPath: string, overwrite: boolean) => Promise<AnalysisImportResult>;
  onPrepareAnalysis: () => Promise<AnalysisRequestResult>;
  onRefreshData: () => void | Promise<void>;
  onRunAiAnalysis?: (jobIds: number[]) => Promise<AiAnalysisRunResult>;
  onStatusChange: (jobId: number, status: JobStatus) => void | Promise<void>;
  manualAnalysisEnabled?: boolean;
  aiAnalysisEnabled?: boolean;
}) {
  const [selectedJobId, setSelectedJobId] = useState<number | null>(jobs[0]?.id ?? null);
  const [selectedJobDetail, setSelectedJobDetail] = useState<Job | null>(jobs[0] ?? null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [modal, setModal] = useState<"prepare" | "import" | null>(null);
  const [prepareLoading, setPrepareLoading] = useState(false);
  const [prepareError, setPrepareError] = useState<string | null>(null);
  const [prepareResult, setPrepareResult] = useState<AnalysisRequestResult | null>(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<AnalysisImportResult | null>(null);
  const [selectedJobIds, setSelectedJobIds] = useState<number[]>([]);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [aiResult, setAiResult] = useState<AiAnalysisRunResult | null>(null);
  const [filters, setFilters] = useState<JobFilters>({
    status: "all",
    source: "all",
    priority: "all",
    location: "all",
    likelyRelevantOnly: true,
    search: "",
  });

  useEffect(() => {
    const refreshedSelection = jobs.find((job) => job.id === selectedJobId) ?? jobs[0] ?? null;
    setSelectedJobId(refreshedSelection?.id ?? null);
    setSelectedJobDetail(refreshedSelection);
    setDetailError(null);
  }, [jobs, selectedJobId, user.id]);

  useEffect(() => {
    const availableJobIds = new Set(jobs.map((job) => job.id));
    setSelectedJobIds((current) => current.filter((jobId) => availableJobIds.has(jobId)));
  }, [jobs]);

  const filteredJobs = useMemo(() => {
    const query = filters.search.trim().toLowerCase();
    return jobs.filter((job) => {
      if (filters.status !== "all" && job.status !== filters.status) return false;
      if (filters.source !== "all" && job.source !== filters.source) return false;
      if (filters.priority !== "all" && (job.codexAnalysis?.priority ?? "Not analyzed") !== filters.priority) return false;
      if (filters.location !== "all" && !job.location.toLowerCase().includes(filters.location.toLowerCase())) return false;
      if (filters.likelyRelevantOnly && !job.likelyRelevant) return false;
      if (query && !`${job.title} ${job.company} ${job.location} ${job.source}`.toLowerCase().includes(query)) return false;
      return true;
    });
  }, [filters, jobs]);

  const selectedJob = selectedJobDetail ?? jobs.find((job) => job.id === selectedJobId) ?? filteredJobs[0] ?? null;

  async function selectJob(job: Job) {
    setSelectedJobId(job.id);
    setSelectedJobDetail(job);
    setDetailError(null);
    try {
      setSelectedJobDetail(await loadJobDetail(job.id));
    } catch {
      setDetailError("Job detail could not be loaded from the API. Showing table data instead.");
    }
  }

  function changeStatus(jobId: number, status: JobStatus) {
    void Promise.resolve(onStatusChange(jobId, status)).then(() => {
      setSelectedJobDetail((current) => (current && current.id === jobId ? { ...current, status } : current));
    });
  }

  async function prepareAnalysis() {
    setPrepareLoading(true);
    setPrepareError(null);
    try {
      setPrepareResult(await onPrepareAnalysis());
    } catch {
      setPrepareError("Analysis request could not be prepared. Check the local API server and database connection.");
    } finally {
      setPrepareLoading(false);
    }
  }

  async function importAnalysis(resultPath: string, overwrite: boolean) {
    setImportLoading(true);
    setImportError(null);
    try {
      setImportResult(await onImportAnalysis(resultPath, overwrite));
    } catch {
      setImportError("Analysis result could not be imported. Check the file path, local API server, and database connection.");
    } finally {
      setImportLoading(false);
    }
  }

  async function runAiAnalysis() {
    setAiResult(null);
    if (!onRunAiAnalysis) {
      setAiError("AI analysis is not available in this mode.");
      return;
    }
    if (selectedJobIds.length === 0) {
      setAiError("Select at least one job before running AI analysis.");
      return;
    }
    setAiLoading(true);
    setAiError(null);
    try {
      setAiResult(await onRunAiAnalysis(selectedJobIds));
    } catch (error) {
      const detail = typeof error === "object" && error !== null && "detail" in error ? error.detail : null;
      const message =
        typeof detail === "string" && detail
          ? detail
          : "AI analysis could not be completed. Check the backend API, AI configuration, and selected jobs.";
      setAiError(message);
    } finally {
      setAiLoading(false);
    }
  }

  return (
    <main className="flex h-[calc(100vh-64px)] flex-1 flex-col gap-lg overflow-hidden p-margin_mobile pb-24 md:h-[calc(100vh-64px)] md:p-margin_desktop">
      <div className="flex shrink-0 flex-col items-start justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h2 className="font-display-lg text-display-lg text-primary">Job Matches</h2>
          <p className="mt-1 font-body-md text-body-md text-on-surface-variant">Reviewing potential roles for {user.displayName}.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {aiAnalysisEnabled ? (
            <button
              className="flex items-center gap-2 rounded-lg border border-outline-variant bg-surface-container-low px-4 py-2 font-label-md text-label-md text-primary transition-colors hover:bg-surface-container-high disabled:cursor-not-allowed disabled:opacity-60"
              disabled={aiLoading}
              onClick={() => void runAiAnalysis()}
              type="button"
            >
              <span className="material-symbols-outlined text-[18px]">psychology</span>
              {aiLoading ? "Running AI..." : `Run AI Analysis${selectedJobIds.length ? ` (${selectedJobIds.length})` : ""}`}
            </button>
          ) : null}
          {manualAnalysisEnabled ? (
            <>
          <button
            className="flex items-center gap-2 rounded-lg border border-outline-variant bg-surface-container-low px-4 py-2 font-label-md text-label-md text-primary transition-colors hover:bg-surface-container-high"
            onClick={() => setModal("prepare")}
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">psychology</span>
            Prepare AI Analysis
          </button>
          <button
            className="flex items-center gap-2 rounded-lg border border-outline-variant bg-surface-container-low px-4 py-2 font-label-md text-label-md text-primary transition-colors hover:bg-surface-container-high"
            onClick={() => setModal("import")}
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">upload</span>
            Import Analysis Result
          </button>
            </>
          ) : null}
          <button
            className="flex items-center gap-2 rounded-lg bg-primary-container px-4 py-2 font-label-md text-label-md text-on-primary transition-opacity hover:opacity-90"
            onClick={() => void onRefreshData()}
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">refresh</span>
            Refresh Data
          </button>
        </div>
      </div>

      {detailError || aiError || aiResult ? (
        <div className="shrink-0 space-y-2" aria-live="polite">
          {detailError ? (
            <div className="rounded-lg border border-error-container bg-surface-container-lowest px-4 py-2 font-body-md text-body-md text-on-error-container">
              {detailError}
            </div>
          ) : null}
          {aiError ? (
            <div className="rounded-lg border border-error-container bg-surface-container-lowest px-4 py-2 font-body-md text-body-md text-on-error-container">
              {aiError}
            </div>
          ) : null}
          {aiResult ? (
            <div className="rounded-lg border border-secondary-container bg-surface-container-lowest px-4 py-2 font-body-md text-body-md text-on-secondary-container">
              AI analysis stored for {aiResult.analyzed_count} job{aiResult.analyzed_count === 1 ? "" : "s"} in batch {aiResult.analysis_batch_id}.
              {aiResult.failed_count ? ` ${aiResult.failed_count} job${aiResult.failed_count === 1 ? "" : "s"} could not be analyzed.` : ""}
              {aiResult.warnings.length ? ` ${aiResult.warnings[0]}` : ""}
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="relative flex flex-1 gap-lg overflow-hidden">
        <section className="flex flex-1 flex-col overflow-hidden rounded-xl border border-surface-variant bg-surface-container-lowest shadow-sm">
          <div className="flex shrink-0 gap-6 border-b border-surface-variant bg-surface-bright px-4">
            {tabs.map((tab) => (
              <button
                className={`py-3 font-label-md text-label-md transition-colors ${
                  filters.status === tab.value
                    ? "border-b-2 border-primary font-bold text-primary"
                    : "text-on-surface-variant hover:text-primary"
                }`}
                key={tab.value}
                onClick={() => setFilters({ ...filters, status: tab.value })}
                type="button"
              >
                {tab.label}
              </button>
            ))}
          </div>
          <FilterBar filters={filters} onChange={setFilters} />
          <JobTable
            jobs={filteredJobs}
            onSelectJob={selectJob}
            onSelectionChange={setSelectedJobIds}
            onStatusChange={changeStatus}
            selectedJobId={selectedJob?.id ?? null}
            selectedJobIds={selectedJobIds}
          />
          <div className="border-t border-surface-variant bg-surface-bright px-4 py-2 font-label-sm text-label-sm text-on-surface-variant lg:hidden">
            Tap a row to select it. The detail drawer is shown on desktop width.
          </div>
        </section>
        <JobDetailDrawer job={selectedJob} onClose={() => setSelectedJobId(null)} onStatusChange={changeStatus} />
      </div>
      {selectedJob ? (
        <section className="rounded-xl border border-surface-variant bg-surface-container-lowest p-4 shadow-sm lg:hidden">
          <div className="mb-2 font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Selected Job</div>
          <div className="font-headline-sm text-headline-sm text-primary">{selectedJob.title}</div>
          <div className="mt-1 font-body-md text-body-md text-on-surface-variant">
            {selectedJob.company} • {getStatusLabel(selectedJob.status)}
          </div>
        </section>
      ) : null}
      {modal === "prepare" ? (
        <PrepareAnalysisModal
          error={prepareError}
          loading={prepareLoading}
          onClose={() => setModal(null)}
          onPrepare={prepareAnalysis}
          result={prepareResult}
          user={user}
        />
      ) : null}
      {modal === "import" ? (
        <ImportAnalysisModal
          error={importError}
          loading={importLoading}
          onClose={() => setModal(null)}
          onImport={importAnalysis}
          result={importResult}
          user={user}
        />
      ) : null}
    </main>
  );
}
