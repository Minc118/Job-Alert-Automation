import SettingsSection from "./SettingsSection";
import type { GmailConnectionStatus } from "../api/authApi";

const sources = ["LinkedIn", "StepStone", "Indeed"];

type GmailConnectionPanelProps = {
  connection?: GmailConnectionStatus | null;
  loading?: boolean;
  notice?: string | null;
  mode?: "mock" | "authenticated";
  onConnect?: () => void;
  onDisconnect?: () => void;
  onFetch?: () => void;
};

function statusLabel(status: string | undefined) {
  if (status === "connected") return "Connected";
  if (status === "token_expired") return "Token expired";
  if (status === "fetch_failed") return "Fetch failed";
  return "Not connected";
}

function statusDot(status: string | undefined) {
  if (status === "connected") return "bg-secondary";
  if (status === "token_expired" || status === "fetch_failed") return "bg-error";
  return "bg-outline";
}

export default function GmailConnectionPanel({
  connection = null,
  loading = false,
  notice = null,
  mode = "mock",
  onConnect,
  onDisconnect,
  onFetch,
}: GmailConnectionPanelProps) {
  const displayedSources = connection?.detectedSources.length ? connection.detectedSources : sources;
  const connected = connection?.status === "connected";

  return (
    <SettingsSection className="lg:col-span-12" icon="mail" title="Gmail Connection">
      <div className="grid grid-cols-1 gap-gutter xl:grid-cols-[minmax(0,1fr)_auto]">
        <div className="grid grid-cols-1 gap-md md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-lg border border-surface-variant bg-surface-container-low p-md">
            <p className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Status</p>
            <p className="mt-sm flex items-center gap-sm font-body-lg text-body-lg font-semibold text-primary">
              <span className={`h-2.5 w-2.5 rounded-full ${statusDot(connection?.status)}`} />
              {loading ? "Checking..." : statusLabel(connection?.status)}
            </p>
          </div>
          <div className="rounded-lg border border-surface-variant bg-surface-container-low p-md">
            <p className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Connected Email</p>
            <p className="mt-sm font-body-md text-body-md text-on-surface">{connection?.connectedEmail ?? "Available after Gmail connection"}</p>
          </div>
          <div className="rounded-lg border border-surface-variant bg-surface-container-low p-md">
            <p className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Last Fetch</p>
            <p className="mt-sm font-body-md text-body-md text-on-surface">{connection?.lastFetchAt ?? "No fetch yet"}</p>
          </div>
          <div className="rounded-lg border border-surface-variant bg-surface-container-low p-md">
            <p className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Scope</p>
            <p className="mt-sm break-all font-body-md text-body-md text-on-surface">{connection?.scope ?? "gmail.readonly"}</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-sm xl:max-w-sm xl:justify-end">
          <button
            className="rounded-lg bg-primary-container px-md py-sm font-label-md text-label-md text-on-primary transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={loading || !onConnect}
            onClick={onConnect}
            type="button"
          >
            {connected ? "Reconnect" : "Connect Gmail"}
          </button>
          <button
            className="rounded-lg border border-outline-variant bg-surface-container-low px-md py-sm font-label-md text-label-md text-primary transition-colors hover:bg-surface-container disabled:cursor-not-allowed disabled:opacity-50"
            disabled={loading || !connected || !onDisconnect}
            onClick={onDisconnect}
            type="button"
          >
            Disconnect
          </button>
          <button
            className="rounded-lg border border-outline-variant bg-surface-container-low px-md py-sm font-label-md text-label-md text-primary opacity-60"
            disabled
            type="button"
          >
            Test Connection
          </button>
          <button
            className="rounded-lg border border-outline-variant bg-surface-container-low px-md py-sm font-label-md text-label-md text-primary transition-colors hover:bg-surface-container disabled:cursor-not-allowed disabled:opacity-50"
            disabled={loading || !connected || !onFetch}
            onClick={onFetch}
            type="button"
          >
            Run Fetch Now
          </button>
        </div>
      </div>

      <div className="mt-lg grid grid-cols-1 gap-md border-t border-surface-variant pt-lg md:grid-cols-[minmax(0,1fr)_auto] md:items-center">
        <div>
          <p className="font-body-md text-body-md text-on-surface">
            The app only reads job alert emails. It does not send, delete, archive, or mark emails as read.
          </p>
          <p className="mt-xs font-label-sm text-label-sm text-on-surface-variant">
            {mode === "authenticated"
              ? "Google login and Gmail readonly OAuth stay separate. Fetch is manual; connection testing and scheduling remain staged."
              : "This panel is UI-only in mock mode. Google login and Gmail readonly OAuth stay separate."}
          </p>
          {notice ? <p className="mt-xs font-label-sm text-label-sm text-secondary">{notice}</p> : null}
        </div>
        <div className="flex flex-wrap gap-sm">
          {displayedSources.map((source) => (
            <span className="rounded-full bg-secondary-container px-3 py-1 font-label-md text-label-md text-on-secondary-fixed-variant" key={source}>
              {source}
            </span>
          ))}
        </div>
      </div>
    </SettingsSection>
  );
}
