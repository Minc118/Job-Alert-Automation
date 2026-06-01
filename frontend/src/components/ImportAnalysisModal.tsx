import { useState } from "react";
import Modal from "./Modal";
import type { AnalysisImportResult, User } from "../types";

export default function ImportAnalysisModal({
  user,
  loading,
  error,
  result,
  onClose,
  onImport,
}: {
  user: User;
  loading: boolean;
  error: string | null;
  result: AnalysisImportResult | null;
  onClose: () => void;
  onImport: (resultPath: string, overwrite: boolean) => void | Promise<void>;
}) {
  const [resultPath, setResultPath] = useState(`output/analysis_results/latest_${user.id}_result.json`);
  const [overwrite, setOverwrite] = useState(false);

  return (
    <Modal onClose={onClose} title="Import Analysis Result">
      <div className="space-y-4 font-body-md text-body-md text-on-surface">
        <p>
          Import a structured JSON result produced by the manual analysis fallback. The local API reads the file from
          <span className="font-mono"> output/analysis_results</span> and writes the analysis rows to Neon.
        </p>
        <label className="block space-y-2">
          <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Result JSON path</span>
          <input
            className="w-full rounded-lg border border-outline-variant bg-surface-container-low px-3 py-2 font-mono text-[12px] text-primary outline-none focus:border-primary focus:ring-1 focus:ring-primary"
            onChange={(event) => setResultPath(event.target.value)}
            type="text"
            value={resultPath}
          />
        </label>
        <label className="flex items-center gap-2 font-body-md text-body-md text-primary">
          <input
            checked={overwrite}
            className="h-4 w-4 rounded border-outline-variant text-primary focus:ring-primary"
            onChange={(event) => setOverwrite(event.target.checked)}
            type="checkbox"
          />
          Allow duplicate batch import with overwrite
        </label>
        <p className="text-on-surface-variant">
          No browser-side AI provider call is made by this dashboard.
        </p>
        {error ? (
          <div className="rounded-lg border border-error-container bg-surface-container-lowest px-3 py-2 text-on-error-container">
            {error}
          </div>
        ) : null}
        {result ? (
          <div className="rounded-lg border border-surface-variant bg-surface-container-low p-3">
            <div className="font-label-md text-label-md text-primary">{result.message}</div>
            <div className="mt-2 grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="font-headline-sm text-headline-sm text-primary">{result.importedCount}</div>
                <div className="font-label-sm text-label-sm text-on-surface-variant">Imported</div>
              </div>
              <div>
                <div className="font-headline-sm text-headline-sm text-primary">{result.skippedCount}</div>
                <div className="font-label-sm text-label-sm text-on-surface-variant">Skipped</div>
              </div>
              <div>
                <div className="font-headline-sm text-headline-sm text-primary">{result.updatedStatusesCount}</div>
                <div className="font-label-sm text-label-sm text-on-surface-variant">Statuses</div>
              </div>
            </div>
            <div className="mt-3 font-mono text-[12px] text-on-surface-variant">{result.resultPath}</div>
          </div>
        ) : null}
        <div className="flex flex-wrap gap-2">
          <button
            className="rounded-lg bg-primary-container px-4 py-2 font-label-md text-label-md text-on-primary disabled:opacity-60"
            disabled={loading}
            onClick={() => onImport(resultPath, overwrite)}
            type="button"
          >
            {loading ? "Importing..." : "Import Result"}
          </button>
          <button
            className="rounded-lg border border-outline-variant bg-surface-container-low px-4 py-2 font-label-md text-label-md text-primary"
            onClick={onClose}
            type="button"
          >
            Close
          </button>
        </div>
      </div>
    </Modal>
  );
}
