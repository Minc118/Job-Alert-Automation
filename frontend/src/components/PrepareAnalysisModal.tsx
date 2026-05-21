import type { AnalysisRequestResult, User } from "../types";
import Modal from "./Modal";

export default function PrepareAnalysisModal({
  error,
  loading,
  onClose,
  onPrepare,
  result,
  user,
}: {
  error: string | null;
  loading: boolean;
  onClose: () => void;
  onPrepare: () => void;
  result: AnalysisRequestResult | null;
  user: User;
}) {
  return (
    <Modal onClose={onClose} title="Prepare Codex Analysis">
      <div className="space-y-4 font-body-md text-body-md text-on-surface">
        <p>
          Prepare a local Markdown and JSON request for {user.displayName}. Open the Markdown file in Codex manually after it is generated.
        </p>
        {result ? (
          <div className="space-y-2 rounded-lg bg-surface-container-low p-3 font-mono text-[12px] text-on-surface-variant">
            <div>analysis_batch_id: {result.analysisBatchId}</div>
            <div>jobs: {result.jobCount}</div>
            <div>{result.requestMarkdownPath}</div>
            <div>{result.requestJsonPath}</div>
          </div>
        ) : (
          <div className="rounded-lg bg-surface-container-low p-3 font-mono text-[12px] text-on-surface-variant">
            output/analysis_requests/latest_{user.id}.md
          </div>
        )}
        {error ? <p className="rounded-lg border border-error-container p-3 text-on-error-container">{error}</p> : null}
        <p className="text-on-surface-variant">No browser-side Codex or AI API call is made.</p>
        <div className="flex gap-2">
          <button
            className="rounded-lg bg-primary-container px-4 py-2 font-label-md text-label-md text-on-primary disabled:opacity-60"
            disabled={loading}
            onClick={onPrepare}
            type="button"
          >
            {loading ? "Preparing..." : result ? "Prepare Again" : "Prepare Request"}
          </button>
          <button className="rounded-lg border border-outline-variant px-4 py-2 font-label-md text-label-md text-primary" onClick={onClose} type="button">
            Close
          </button>
        </div>
      </div>
    </Modal>
  );
}
