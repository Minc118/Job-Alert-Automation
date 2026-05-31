import type { GeminiAnalysisRunResult, IngestionRun, Job, OverviewData, User, UserPreferences } from "../types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

export interface AuthenticatedApiUser {
  subject: string;
  displayName: string | null;
  email: string | null;
}

export interface MeResponse {
  authenticated: boolean;
  authProvider: "neon";
  user: AuthenticatedApiUser;
  appUser: User;
  accountDataReady: boolean;
  onboardingComplete: boolean;
}

export interface GmailConnectionStatus {
  status: "connected" | "not_connected" | "token_expired" | "fetch_failed" | string;
  connectedEmail: string | null;
  lastFetchAt: string | null;
  scope: string;
  detectedSources: string[];
}

export interface GmailFetchSummary {
  ingestionRunId: number;
  emailsFetched: number;
  jobsParsed: number;
  uniqueJobs: number;
  newlyDiscovered: number;
  seenAgain: number;
  likelyRelevant: number;
}

export interface AuthenticatedDocument {
  id: number;
  userId: string;
  documentType: "profile_markdown" | "resume_pdf" | "cover_letter_template";
  originalFilename: string;
  mimeType: string | null;
  fileSizeBytes: number | null;
  isActive: boolean;
  createdAt: string;
}

export interface AuthenticatedDocumentPreview {
  documentId: number;
  documentType: "profile_markdown" | "cover_letter_template";
  content: string;
  truncated: boolean;
}

async function authenticatedJson<T>(path: string, identityToken: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/api${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${identityToken}`,
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getMe(identityToken: string): Promise<MeResponse> {
  return authenticatedJson("/me", identityToken);
}

export function getAuthenticatedOverview(identityToken: string, range = "latest_run"): Promise<OverviewData> {
  return authenticatedJson(`/overview?range=${encodeURIComponent(range)}`, identityToken);
}

export function getAuthenticatedJobs(identityToken: string, range = "latest_run"): Promise<Job[]> {
  return authenticatedJson(`/jobs?range=${encodeURIComponent(range)}`, identityToken);
}

export function getAuthenticatedJob(identityToken: string, jobId: number): Promise<Job> {
  return authenticatedJson(`/jobs/${jobId}`, identityToken);
}

export function getAuthenticatedRuns(identityToken: string): Promise<IngestionRun[]> {
  return authenticatedJson("/runs", identityToken);
}

export function updateAuthenticatedJobStatus(identityToken: string, jobId: number, status: Job["status"]) {
  return authenticatedJson<{ userId: string; jobId: number; status: Job["status"] }>(`/user-jobs/${jobId}/status`, identityToken, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
}

export function getAuthenticatedPreferences(identityToken: string): Promise<UserPreferences> {
  return authenticatedJson("/user/preferences", identityToken);
}

export function updateAuthenticatedPreferences(
  identityToken: string,
  preferences: Pick<UserPreferences, "targetRoleKeywords" | "preferredLocations" | "excludedKeywords">,
): Promise<UserPreferences> {
  return authenticatedJson("/user/preferences", identityToken, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(preferences),
  });
}

export function completeAuthenticatedOnboarding(identityToken: string): Promise<{ userId: string; onboardingComplete: boolean }> {
  return authenticatedJson("/onboarding/complete", identityToken, {
    method: "POST",
  });
}

export function getAuthenticatedGmailStatus(identityToken: string): Promise<GmailConnectionStatus> {
  return authenticatedJson("/gmail/status", identityToken);
}

export function startAuthenticatedGmailConnect(identityToken: string): Promise<{ authorizationUrl: string }> {
  return authenticatedJson("/gmail/connect", identityToken, {
    method: "POST",
  });
}

export function disconnectAuthenticatedGmail(identityToken: string): Promise<GmailConnectionStatus> {
  return authenticatedJson("/gmail/disconnect", identityToken, {
    method: "POST",
  });
}

export function runAuthenticatedGmailFetch(identityToken: string): Promise<GmailFetchSummary> {
  return authenticatedJson("/gmail/fetch", identityToken, {
    method: "POST",
  });
}

export function runAuthenticatedGeminiAnalysis(identityToken: string, jobIds: number[]): Promise<GeminiAnalysisRunResult> {
  return authenticatedJson("/analysis/run", identityToken, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jobIds }),
  });
}

export function getAuthenticatedDocuments(identityToken: string): Promise<AuthenticatedDocument[]> {
  return authenticatedJson("/user/documents", identityToken);
}

export function uploadAuthenticatedDocument(
  identityToken: string,
  documentType: AuthenticatedDocument["documentType"],
  file: File,
): Promise<AuthenticatedDocument> {
  const formData = new FormData();
  formData.append("documentType", documentType);
  formData.append("file", file);
  return authenticatedJson("/user/documents", identityToken, {
    method: "POST",
    body: formData,
  });
}

export function activateAuthenticatedDocument(identityToken: string, documentId: number): Promise<AuthenticatedDocument> {
  return authenticatedJson(`/user/documents/${documentId}/activate`, identityToken, {
    method: "PATCH",
  });
}

export function deleteAuthenticatedDocument(identityToken: string, documentId: number): Promise<{ documentId: number; deleted: boolean }> {
  return authenticatedJson(`/user/documents/${documentId}`, identityToken, {
    method: "DELETE",
  });
}

export function previewAuthenticatedDocument(identityToken: string, documentId: number): Promise<AuthenticatedDocumentPreview> {
  return authenticatedJson(`/user/documents/${documentId}/preview`, identityToken);
}
