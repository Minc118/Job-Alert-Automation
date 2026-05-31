import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  disconnectAuthenticatedGmail,
  activateAuthenticatedDocument,
  deleteAuthenticatedDocument,
  getAuthenticatedDocuments,
  getAuthenticatedGmailStatus,
  getMe,
  previewAuthenticatedDocument,
  runAuthenticatedGmailFetch,
  startAuthenticatedGmailConnect,
  uploadAuthenticatedDocument,
  AuthenticatedApiError,
  type AuthenticatedDocument,
  type AuthenticatedDocumentPreview,
  type GmailConnectionStatus,
  type MeResponse,
} from "../api/authApi";
import { useAuth } from "../auth/AuthProvider";
import AuthenticatedDocumentsSection from "../components/AuthenticatedDocumentsSection";
import GmailConnectionPanel from "../components/GmailConnectionPanel";
import SettingsSection from "../components/SettingsSection";
import SystemNotesCard from "../components/SystemNotesCard";

export default function AuthAccountSettingsPage({ onDashboardRefresh }: { onDashboardRefresh?: () => Promise<void> }) {
  const auth = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [backendIdentity, setBackendIdentity] = useState<MeResponse | null>(null);
  const [identityStatus, setIdentityStatus] = useState<"loading" | "verified" | "unavailable">("loading");
  const [gmailConnection, setGmailConnection] = useState<GmailConnectionStatus | null>(null);
  const [gmailLoading, setGmailLoading] = useState(false);
  const [gmailNotice, setGmailNotice] = useState<string | null>(
    searchParams.get("gmail") === "connected" ? "Gmail readonly authorization was stored for this app account." : null,
  );
  const [documents, setDocuments] = useState<AuthenticatedDocument[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentsNotice, setDocumentsNotice] = useState<string | null>(null);
  const [documentPreview, setDocumentPreview] = useState<AuthenticatedDocumentPreview | null>(null);

  useEffect(() => {
    let active = true;
    setIdentityStatus("loading");

    auth
      .getIdentityToken()
      .then((identityToken) => {
        if (!identityToken) {
          throw new Error("Missing identity token.");
        }
        return getMe(identityToken);
      })
      .then((me) => {
        if (!active) return;
        setBackendIdentity(me);
        setIdentityStatus("verified");
      })
      .catch(() => {
        if (!active) return;
        setBackendIdentity(null);
        setIdentityStatus("unavailable");
      });

    return () => {
      active = false;
    };
  }, [auth]);

  async function signOut() {
    await auth.signOut();
    navigate("/");
  }

  async function withIdentityToken<T>(work: (identityToken: string) => Promise<T>) {
    const identityToken = await auth.getIdentityToken();
    if (!identityToken) {
      throw new Error("Missing identity token.");
    }
    return work(identityToken);
  }

  async function loadGmailConnection() {
    setGmailLoading(true);
    try {
      const connection = await withIdentityToken(getAuthenticatedGmailStatus);
      setGmailConnection(connection);
    } catch {
      setGmailConnection(null);
      setGmailNotice("Gmail status could not be loaded. Start the local API and check Gmail OAuth configuration before connecting.");
    } finally {
      setGmailLoading(false);
    }
  }

  useEffect(() => {
    void loadGmailConnection();
    void loadDocuments();
  }, []);

  async function loadDocuments() {
    setDocumentsLoading(true);
    try {
      setDocuments(await withIdentityToken(getAuthenticatedDocuments));
    } catch {
      setDocuments([]);
      setDocumentsNotice("Private document metadata could not be loaded. Start the local API and verify account access.");
    } finally {
      setDocumentsLoading(false);
    }
  }

  async function connectGmail() {
    setGmailLoading(true);
    setGmailNotice(null);
    try {
      const { authorizationUrl } = await withIdentityToken(startAuthenticatedGmailConnect);
      window.location.assign(authorizationUrl);
    } catch {
      setGmailNotice("Gmail connection could not be started. Check the local API and Gmail OAuth settings.");
      setGmailLoading(false);
    }
  }

  async function disconnectGmail() {
    setGmailLoading(true);
    setGmailNotice(null);
    try {
      const connection = await withIdentityToken(disconnectAuthenticatedGmail);
      setGmailConnection(connection);
      setGmailNotice("Gmail connection metadata was removed for this app account.");
    } catch {
      setGmailNotice("Gmail disconnect could not be completed. Check the local API and try again.");
    } finally {
      setGmailLoading(false);
    }
  }

  async function fetchGmailNow() {
    setGmailLoading(true);
    setGmailNotice(null);
    try {
      const summary = await withIdentityToken(runAuthenticatedGmailFetch);
      await loadGmailConnection();
      await onDashboardRefresh?.();
      const warningText = summary.warnings.length ? ` ${summary.warnings.join(" ")}` : "";
      setGmailNotice(
        `Fetch run ${summary.run_id} completed: ${summary.scanned_message_count} message(s), ${summary.parsed_job_count} parsed job(s), ${summary.new_job_count} newly discovered, ${summary.seen_before_count} seen before, ${summary.skipped_count} skipped.${warningText}`,
      );
    } catch (error) {
      setGmailNotice(
        error instanceof AuthenticatedApiError && error.detail
          ? error.detail
          : "Gmail fetch could not be completed. Connect or reconnect Gmail, then try again.",
      );
    } finally {
      setGmailLoading(false);
    }
  }

  async function uploadDocument(documentType: AuthenticatedDocument["documentType"], file: File) {
    setDocumentsLoading(true);
    setDocumentsNotice(null);
    setDocumentPreview(null);
    try {
      await withIdentityToken((token) => uploadAuthenticatedDocument(token, documentType, file));
      await loadDocuments();
      setDocumentsNotice("Private document upload completed and the new document is active.");
    } catch {
      setDocumentsNotice("Private document upload failed. Use Markdown for profile summaries and PDF for resumes.");
    } finally {
      setDocumentsLoading(false);
    }
  }

  async function activateDocument(documentId: number) {
    setDocumentsLoading(true);
    setDocumentsNotice(null);
    try {
      await withIdentityToken((token) => activateAuthenticatedDocument(token, documentId));
      await loadDocuments();
      setDocumentsNotice("Active document updated.");
    } catch {
      setDocumentsNotice("Document activation failed. Check the local API and try again.");
    } finally {
      setDocumentsLoading(false);
    }
  }

  async function deleteDocument(documentId: number) {
    setDocumentsLoading(true);
    setDocumentsNotice(null);
    setDocumentPreview(null);
    try {
      await withIdentityToken((token) => deleteAuthenticatedDocument(token, documentId));
      await loadDocuments();
      setDocumentsNotice("Private document deleted.");
    } catch {
      setDocumentsNotice("Document deletion failed. Check the local API and try again.");
    } finally {
      setDocumentsLoading(false);
    }
  }

  async function previewDocument(documentId: number) {
    setDocumentsLoading(true);
    setDocumentsNotice(null);
    try {
      setDocumentPreview(await withIdentityToken((token) => previewAuthenticatedDocument(token, documentId)));
    } catch {
      setDocumentPreview(null);
      setDocumentsNotice("Markdown preview could not be loaded.");
    } finally {
      setDocumentsLoading(false);
    }
  }

  return (
    <main className="flex-1 p-margin_mobile pb-24 md:p-margin_desktop">
      <div className="mb-xl">
        <h2 className="mb-2 font-display-lg text-display-lg text-primary">Settings</h2>
        <p className="font-body-lg text-body-lg text-on-surface-variant">Manage the authenticated app account boundary and staged integrations.</p>
      </div>

      <div className="grid grid-cols-1 gap-gutter lg:grid-cols-12">
        <SettingsSection className="lg:col-span-12" icon="account_circle" title="App Account">
          <div className="flex flex-col gap-md md:flex-row md:items-end md:justify-between">
            <div className="space-y-sm">
              <div>
                <span className="block font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Signed In</span>
                <span className="font-body-lg text-body-lg text-primary">{auth.user?.displayName ?? "Neon Auth user"}</span>
              </div>
              <p className="max-w-3xl font-body-md text-body-md text-on-surface-variant">
                Google login identifies this app account. Gmail job alert access is connected separately and uses readonly permission for manual job alert
                fetching.
              </p>
            </div>
            <button
              className="inline-flex items-center justify-center gap-sm rounded-lg border border-outline-variant bg-surface px-lg py-md font-label-md text-label-md text-primary hover:bg-surface-container"
              onClick={() => void signOut()}
              type="button"
            >
              <span className="material-symbols-outlined text-[18px]">logout</span>
              Sign Out
            </button>
          </div>
        </SettingsSection>

        <SettingsSection className="lg:col-span-12" icon="link_off" title="Account Data Status">
          <div className="space-y-md">
            <div className="flex flex-wrap items-center gap-sm">
              <span className="font-label-md text-label-md uppercase tracking-wider text-on-surface-variant">FastAPI identity</span>
              {identityStatus === "loading" ? (
                <span className="rounded-full bg-surface-container px-sm py-xs font-label-sm text-label-sm text-on-surface-variant">Checking...</span>
              ) : null}
              {identityStatus === "verified" ? (
                <span className="rounded-full bg-secondary-container px-sm py-xs font-label-sm text-label-sm text-on-secondary-container">Verified</span>
              ) : null}
              {identityStatus === "unavailable" ? (
                <span className="rounded-full border border-error-container bg-surface px-sm py-xs font-label-sm text-label-sm text-on-error-container">
                  Backend validation unavailable
                </span>
              ) : null}
            </div>
            {backendIdentity ? (
              <p className="font-body-md text-body-md text-on-surface-variant">
                FastAPI validated the Neon Auth subject <span className="font-medium text-primary">{backendIdentity.user.subject}</span> and mapped it to app
                profile <span className="font-medium text-primary">{backendIdentity.appUser.id}</span>. Job and run views now use this account-scoped profile;
                onboarding preferences and manual Gmail fetch batches are scoped through this profile while document hardening continues later.
              </p>
            ) : (
              <p className="font-body-md text-body-md text-on-surface-variant">
                Start the local API and configure backend Neon Auth JWKS verification to validate this browser session. Account-scoped dashboard data remains
                disabled until validation and ownership mapping are in place.
              </p>
            )}
          </div>
        </SettingsSection>

        <GmailConnectionPanel
          connection={gmailConnection}
          loading={gmailLoading}
          mode="authenticated"
          notice={gmailNotice}
          onConnect={() => void connectGmail()}
          onDisconnect={() => void disconnectGmail()}
          onFetch={() => void fetchGmailNow()}
        />

        <AuthenticatedDocumentsSection
          documents={documents}
          loading={documentsLoading}
          notice={documentsNotice}
          onActivate={(documentId) => void activateDocument(documentId)}
          onDelete={(documentId) => void deleteDocument(documentId)}
          onPreview={(documentId) => void previewDocument(documentId)}
          onUpload={(documentType, file) => void uploadDocument(documentType, file)}
          preview={documentPreview}
        />

        <SystemNotesCard />
      </div>
    </main>
  );
}
