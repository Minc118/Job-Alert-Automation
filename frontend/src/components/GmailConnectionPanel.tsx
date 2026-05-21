import SettingsSection from "./SettingsSection";

const mockActions = ["Connect Gmail", "Reconnect", "Disconnect", "Test Connection", "Run Fetch Now"];
const sources = ["LinkedIn", "StepStone", "Indeed"];

export default function GmailConnectionPanel() {
  return (
    <SettingsSection className="lg:col-span-12" icon="mail" title="Gmail Connection">
      <div className="grid grid-cols-1 gap-gutter xl:grid-cols-[minmax(0,1fr)_auto]">
        <div className="grid grid-cols-1 gap-md md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-lg border border-surface-variant bg-surface-container-low p-md">
            <p className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Status</p>
            <p className="mt-sm flex items-center gap-sm font-body-lg text-body-lg font-semibold text-primary">
              <span className="h-2.5 w-2.5 rounded-full bg-outline" />
              Not connected
            </p>
          </div>
          <div className="rounded-lg border border-surface-variant bg-surface-container-low p-md">
            <p className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Connected Email</p>
            <p className="mt-sm font-body-md text-body-md text-on-surface">Available after Gmail connection</p>
          </div>
          <div className="rounded-lg border border-surface-variant bg-surface-container-low p-md">
            <p className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Last Fetch</p>
            <p className="mt-sm font-body-md text-body-md text-on-surface">No multi-user fetch yet</p>
          </div>
          <div className="rounded-lg border border-surface-variant bg-surface-container-low p-md">
            <p className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Scope</p>
            <p className="mt-sm font-body-md text-body-md text-on-surface">gmail.readonly</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-sm xl:max-w-sm xl:justify-end">
          {mockActions.map((action, index) => (
            <button
              className={`rounded-lg px-md py-sm font-label-md text-label-md transition-colors ${
                index === 0
                  ? "bg-primary-container text-on-primary hover:opacity-90"
                  : "border border-outline-variant bg-surface-container-low text-primary hover:bg-surface-container"
              }`}
              key={action}
              type="button"
            >
              {action}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-lg grid grid-cols-1 gap-md border-t border-surface-variant pt-lg md:grid-cols-[minmax(0,1fr)_auto] md:items-center">
        <div>
          <p className="font-body-md text-body-md text-on-surface">
            The app only reads job alert emails. It does not send, delete, archive, or mark emails as read.
          </p>
          <p className="mt-xs font-label-sm text-label-sm text-on-surface-variant">
            This panel is UI-only in UI-PUBLIC1. Google login and Gmail readonly OAuth stay separate.
          </p>
        </div>
        <div className="flex flex-wrap gap-sm">
          {sources.map((source) => (
            <span className="rounded-full bg-secondary-container px-3 py-1 font-label-md text-label-md text-on-secondary-fixed-variant" key={source}>
              {source}
            </span>
          ))}
        </div>
      </div>
    </SettingsSection>
  );
}
