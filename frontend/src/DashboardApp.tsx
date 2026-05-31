import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "./auth/AuthProvider";
import AppShell from "./components/AppShell";
import { client, apiMode, type DashboardClient } from "./api/client";
import {
  getAuthenticatedJob,
  getAuthenticatedJobs,
  getAuthenticatedOverview,
  getAuthenticatedRuns,
  getMe,
  runAuthenticatedGeminiAnalysis,
  updateAuthenticatedJobStatus,
} from "./api/authApi";
import { mockClient } from "./api/mockClient";
import { dataSources as initialDataSources, documents as initialDocuments, ingestionRuns, jobs as initialJobs, preferences, users as fallbackUsers } from "./data/mockData";
import JobsPage from "./pages/JobsPage";
import OverviewPage from "./pages/OverviewPage";
import SettingsPage from "./pages/SettingsPage";
import AuthAccountSettingsPage from "./pages/AuthAccountSettingsPage";
import type { AnalysisImportResult, AnalysisRequestResult, DataSourceStatus, IngestionRun, Job, JobStatus, OverviewData, Page, User, UserDocument, UserId, UserPreferences } from "./types";

const API_UNAVAILABLE_MESSAGE = "API unavailable. Switch to mock mode or start the local API server.";

function fetchDashboardData(dashboardClient: DashboardClient, userId: UserId) {
  return Promise.all([
    dashboardClient.getJobs(userId, "latest_run"),
    dashboardClient.getRuns(userId),
    dashboardClient.getOverview(userId, "latest_run"),
    dashboardClient.getPreferences(userId),
    dashboardClient.getDocuments(userId),
    dashboardClient.getDataSources(),
  ]);
}

function fetchAuthenticatedDashboardData(identityToken: string) {
  return Promise.all([
    getAuthenticatedJobs(identityToken, "latest_run"),
    getAuthenticatedRuns(identityToken),
    getAuthenticatedOverview(identityToken, "latest_run"),
  ]);
}

function pageFromPath(pathname: string): Page {
  if (pathname.endsWith("/jobs")) return "jobs";
  if (pathname.endsWith("/settings")) return "settings";
  return "overview";
}

export default function DashboardApp({ mode }: { mode: "app" | "demo" }) {
  const auth = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const page = pageFromPath(location.pathname);
  const dashboardClient = mode === "demo" ? mockClient : client;
  const needsAuthScopedBackend = mode === "app" && auth.mode === "neon";
  const basePath = mode === "demo" ? "/demo" : "/app";
  const modeLabel = mode === "demo" ? "demo mock" : apiMode;
  const [selectedUserId, setSelectedUserId] = useState<UserId>(fallbackUsers[0]?.id ?? "demo-alex");
  const [appUsers, setAppUsers] = useState<User[]>(fallbackUsers);
  const [jobs, setJobs] = useState<Job[]>(initialJobs);
  const [runs, setRuns] = useState<IngestionRun[]>(ingestionRuns);
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [userPreference, setUserPreference] = useState<UserPreferences>(preferences[0]);
  const [userDocuments, setUserDocuments] = useState<UserDocument[]>(
    initialDocuments.filter((document) => document.userId === (fallbackUsers[0]?.id ?? "demo-alex")),
  );
  const [sourceStatuses, setSourceStatuses] = useState<DataSourceStatus[]>(initialDataSources);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [identityToken, setIdentityToken] = useState<string | null>(null);

  useEffect(() => {
    if (needsAuthScopedBackend) {
      setAppUsers(fallbackUsers);
      return;
    }
    let active = true;
    dashboardClient
      .getUsers()
      .then((loadedUsers) => {
        if (!active) return;
        setAppUsers(loadedUsers.length ? loadedUsers : fallbackUsers);
      })
      .catch(() => {
        if (!active) return;
        if (mode !== "demo" && apiMode === "real") {
          setErrorMessage(API_UNAVAILABLE_MESSAGE);
        }
        setAppUsers(fallbackUsers);
      });
    return () => {
      active = false;
    };
  }, [dashboardClient, mode, needsAuthScopedBackend]);

  useEffect(() => {
    if (needsAuthScopedBackend) {
      let active = true;
      setLoading(true);
      setErrorMessage(null);
      auth
        .getIdentityToken()
        .then(async (token) => {
          if (!token) throw new Error("Missing identity token.");
          const [me, [loadedJobs, loadedRuns, loadedOverview]] = await Promise.all([getMe(token), fetchAuthenticatedDashboardData(token)]);
          return { me, loadedJobs, loadedRuns, loadedOverview, token };
        })
        .then(({ me, loadedJobs, loadedRuns, loadedOverview, token }) => {
          if (!active) return;
          setIdentityToken(token);
          setSelectedUserId(me.appUser.id);
          setAppUsers([me.appUser]);
          setJobs(loadedJobs);
          setRuns(loadedRuns);
          setOverview(loadedOverview);
          setUserDocuments([]);
          setSourceStatuses([]);
        })
        .catch(() => {
          if (!active) return;
          setIdentityToken(null);
          setJobs([]);
          setRuns([]);
          setOverview(null);
          setErrorMessage("Authenticated dashboard data could not be loaded. Start the local API and verify Neon Auth backend configuration.");
        })
        .finally(() => {
          if (active) setLoading(false);
        });
      return () => {
        active = false;
      };
    }
    let active = true;
    setLoading(true);
    setErrorMessage(null);
    fetchDashboardData(dashboardClient, selectedUserId)
      .then(([loadedJobs, loadedRuns, loadedOverview, loadedPreference, loadedDocuments, loadedSources]) => {
        if (!active) return;
        setJobs(loadedJobs);
        setRuns(loadedRuns);
        setOverview(loadedOverview);
        setUserPreference(loadedPreference);
        setUserDocuments(loadedDocuments);
        setSourceStatuses(loadedSources);
      })
      .catch(() => {
        if (!active) return;
        setJobs([]);
        setRuns([]);
        setOverview(null);
        setErrorMessage(mode !== "demo" && apiMode === "real" ? API_UNAVAILABLE_MESSAGE : "Mock data could not be loaded.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [auth, dashboardClient, mode, needsAuthScopedBackend, selectedUserId]);

  const selectedUser = appUsers.find((user) => user.id === selectedUserId) ??
    (needsAuthScopedBackend
      ? { id: selectedUserId, displayName: auth.user?.displayName ?? "Signed In User" }
      : fallbackUsers[0]);
  const userJobs = useMemo(() => jobs.filter((job) => job.userId === selectedUserId), [jobs, selectedUserId]);
  const latestRun = runs
    .filter((run) => run.userId === selectedUserId)
    .sort((a, b) => b.startedAt.localeCompare(a.startedAt))[0];

  async function refreshSelectedUserData() {
    setLoading(true);
    setErrorMessage(null);
    try {
      if (needsAuthScopedBackend) {
        const token = identityToken ?? (await auth.getIdentityToken());
        if (!token) throw new Error("Missing identity token.");
        const [loadedJobs, loadedRuns, loadedOverview] = await fetchAuthenticatedDashboardData(token);
        setIdentityToken(token);
        setJobs(loadedJobs);
        setRuns(loadedRuns);
        setOverview(loadedOverview);
        return;
      }
      const [loadedJobs, loadedRuns, loadedOverview, loadedPreference, loadedDocuments, loadedSources] =
        await fetchDashboardData(dashboardClient, selectedUserId);
      setJobs(loadedJobs);
      setRuns(loadedRuns);
      setOverview(loadedOverview);
      setUserPreference(loadedPreference);
      setUserDocuments(loadedDocuments);
      setSourceStatuses(loadedSources);
    } catch {
      setJobs([]);
      setRuns([]);
      setOverview(null);
      setErrorMessage(mode !== "demo" && apiMode === "real" ? API_UNAVAILABLE_MESSAGE : "Mock data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  async function updateStatus(jobId: number, status: JobStatus) {
    setErrorMessage(null);
    try {
      if (needsAuthScopedBackend) {
        const token = identityToken ?? (await auth.getIdentityToken());
        if (!token) throw new Error("Missing identity token.");
        await updateAuthenticatedJobStatus(token, jobId, status);
        setIdentityToken(token);
      } else {
        await dashboardClient.updateJobStatus(selectedUserId, jobId, status);
      }
      setJobs((current) => current.map((job) => (job.id === jobId ? { ...job, status } : job)));
      setOverview((current) =>
        current
          ? { ...current, topRecommendedJobs: current.topRecommendedJobs.map((job) => (job.id === jobId ? { ...job, status } : job)) }
          : current,
      );
    } catch {
      setErrorMessage(mode !== "demo" && apiMode === "real" ? "Status update failed. Check the local API server and database connection." : "Status update failed.");
    }
  }

  function loadJobDetail(jobId: number): Promise<Job> {
    if (needsAuthScopedBackend && identityToken) {
      return getAuthenticatedJob(identityToken, jobId);
    }
    return dashboardClient.getJob(selectedUserId, jobId);
  }

  function prepareAnalysisRequest(): Promise<AnalysisRequestResult> {
    return dashboardClient.prepareAnalysisRequest(selectedUserId);
  }

  async function importAnalysisResult(resultPath: string, overwrite: boolean): Promise<AnalysisImportResult> {
    const result = await dashboardClient.importAnalysisResult(resultPath, overwrite);
    await refreshSelectedUserData();
    return result;
  }

  async function runGeminiAnalysis(jobIds: number[]) {
    const token = identityToken ?? (await auth.getIdentityToken());
    if (!token) throw new Error("Missing identity token.");
    const result = await runAuthenticatedGeminiAnalysis(token, jobIds);
    setIdentityToken(token);
    await refreshSelectedUserData();
    return result;
  }

  return (
    <AppShell
      onNavigate={(nextPage) => navigate(`${basePath}/${nextPage}`)}
      onRefreshData={refreshSelectedUserData}
      onUserChange={setSelectedUserId}
      page={page}
      selectedUserId={selectedUserId}
      showRefreshData
      showUserSwitcher={!needsAuthScopedBackend}
      signedInDisplayName={auth.user?.displayName}
      users={appUsers}
    >
      {needsAuthScopedBackend ? (
        page === "settings" ? (
          <AuthAccountSettingsPage onDashboardRefresh={refreshSelectedUserData} />
        ) : (
          <>
            <div className="px-margin_mobile pt-3 md:px-margin_desktop">
              <div className="flex flex-wrap items-center gap-2 font-label-sm text-label-sm text-on-surface-variant">
                <span className="rounded-full bg-secondary-container px-2 py-1 text-on-secondary-container">Authenticated account data</span>
                {loading ? <span className="rounded-full bg-surface-container-low px-2 py-1">Loading...</span> : null}
              </div>
              {errorMessage ? (
                <div className="mt-3 rounded-lg border border-error-container bg-surface-container-lowest px-4 py-3 font-body-md text-body-md text-on-error-container">
                  {errorMessage}
                </div>
              ) : null}
            </div>
            {page === "overview" ? (
              <OverviewPage jobs={userJobs} latestRun={latestRun} onViewJobs={() => navigate(`${basePath}/jobs`)} overview={overview} user={selectedUser} />
            ) : null}
            {page === "jobs" ? (
              <JobsPage
                jobs={userJobs}
                loadJobDetail={loadJobDetail}
                geminiAnalysisEnabled
                manualAnalysisEnabled={false}
                onImportAnalysis={importAnalysisResult}
                onPrepareAnalysis={prepareAnalysisRequest}
                onRefreshData={refreshSelectedUserData}
                onRunGeminiAnalysis={runGeminiAnalysis}
                onStatusChange={updateStatus}
                user={selectedUser}
              />
            ) : null}
          </>
        )
      ) : (
        <>
      <div className="px-margin_mobile pt-3 md:px-margin_desktop">
        <div className="flex flex-wrap items-center gap-2 font-label-sm text-label-sm text-on-surface-variant">
          <span className="rounded-full bg-surface-container-low px-2 py-1">Data mode: {modeLabel}</span>
          {mode === "demo" ? <span className="rounded-full bg-secondary-container px-2 py-1 text-on-secondary-container">Public demo, mock data only</span> : null}
          {loading ? <span className="rounded-full bg-surface-container-low px-2 py-1">Loading...</span> : null}
        </div>
        {errorMessage ? (
          <div className="mt-3 rounded-lg border border-error-container bg-surface-container-lowest px-4 py-3 font-body-md text-body-md text-on-error-container">
            {errorMessage}
          </div>
        ) : null}
      </div>
      {page === "overview" ? <OverviewPage jobs={userJobs} latestRun={latestRun} onViewJobs={() => navigate(`${basePath}/jobs`)} overview={overview} user={selectedUser} /> : null}
      {page === "jobs" ? (
        <JobsPage
          jobs={userJobs}
          loadJobDetail={loadJobDetail}
          onImportAnalysis={importAnalysisResult}
          onPrepareAnalysis={prepareAnalysisRequest}
          onRefreshData={refreshSelectedUserData}
          onStatusChange={updateStatus}
          user={selectedUser}
        />
      ) : null}
      {page === "settings" ? <SettingsPage dataSources={sourceStatuses} documents={userDocuments} preferences={userPreference} user={selectedUser} /> : null}
        </>
      )}
    </AppShell>
  );
}
