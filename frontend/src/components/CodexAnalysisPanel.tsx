import type { CodexJobAnalysis } from "../types";

function scoreColor(priority: string) {
  if (priority === "High") return "bg-[#10b981]";
  if (priority === "Medium") return "bg-[#f59e0b]";
  if (priority === "Low") return "bg-[#ef4444]";
  return "bg-outline";
}

export default function CodexAnalysisPanel({ analysis }: { analysis?: CodexJobAnalysis }) {
  const priority = analysis?.priority ?? "Not analyzed";
  const score = analysis?.score == null ? null : Math.round(analysis.score * 10);

  return (
    <section className="overflow-hidden rounded-xl border border-surface-variant bg-surface-bright shadow-[0_2px_8px_rgba(0,0,0,0.02)]">
      <div className="flex items-center gap-2 border-b border-surface-variant bg-surface-container-low p-3">
        <span className="material-symbols-outlined text-[18px] text-primary">psychology</span>
        <h4 className="font-label-sm text-label-sm font-bold uppercase tracking-wider text-primary">Codex Analysis</h4>
      </div>
      <div className="flex flex-col gap-4 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`h-3 w-3 rounded-full ${scoreColor(priority)}`} />
            <span className="font-headline-md text-headline-md font-bold text-primary">{priority}</span>
          </div>
          <div className="text-right">
            <span className="text-3xl font-light tracking-tighter text-primary">
              {score ?? "--"}
              <span className="text-lg text-on-surface-variant">/100</span>
            </span>
          </div>
        </div>
        <div>
          <h5 className="mb-1 text-[11px] font-bold uppercase text-on-surface-variant">Reasoning</h5>
          <p className="rounded-lg border border-surface-variant bg-surface-container-low p-3 font-body-md text-body-md leading-relaxed text-primary">
            {analysis?.reason ?? "No Codex analysis has been imported for this job yet."}
          </p>
        </div>
        <div>
          <h5 className="mb-1 flex items-center gap-1 text-[11px] font-bold uppercase text-on-error-container">
            <span className="material-symbols-outlined text-[14px]">warning</span>
            Concern
          </h5>
          <p className="text-[13px] font-body-md text-on-surface-variant">
            {analysis?.concern ?? "No concern recorded."}
          </p>
        </div>
      </div>
    </section>
  );
}
