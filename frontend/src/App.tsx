import { useEffect, useMemo, useState } from "react";
import AppShell from "./components/AppShell";
import { dataSources as initialDataSources, documents as initialDocuments, ingestionRuns, jobs as initialJobs, preferences, users as fallbackUsers } from "./data/mockData";
import { apiMode, client } from "./api/client";
import JobsPage from "./pages/JobsPage";
import OverviewPage from "./pages/OverviewPage";
import SettingsPage from "./pages/SettingsPage";
import type { AnalysisImportResult, AnalysisRequestResult, DataSourceStatus, IngestionRun, Job, JobStatus, OverviewData, Page, User, UserDocument, UserId, UserPreferences } from "./types";

const API_UNAVAILABLE_MESSAGE = "API unavailable. Switch to mock mode or start the local API server.";

function fetchDashboardData(userId: UserId) {
  return Promise.all([
    client.getJobs(userId, "latest_run"),
    client.getRuns(userId),
    client.getOverview(userId, "latest_run"),
    client.getPreferences(userId),
    client.getDocuments(userId),
    client.getDataSources(),
  ]);
}

export default function App() {
  const [page, setPage] = useState<Page>("overview");
  const [selectedUserId, setSelectedUserId] = useState<UserId>("minjian");
  const [appUsers, setAppUsers] = useState<User[]>(fallbackUsers);
  const [jobs, setJobs] = useState<Job[]>(initialJobs);
  const [runs, setRuns] = useState<IngestionRun[]>(ingestionRuns);
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [userPreference, setUserPreference] = useState<UserPreferences>(preferences[0]);
  const [userDocuments, setUserDocuments] = useState<UserDocument[]>(initialDocuments.filter((document) => document.userId === "minjian"));
  const [sourceStatuses, setSourceStatuses] = useState<DataSourceStatus[]>(initialDataSources);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    client
      .getUsers()
      .then((loadedUsers) => {
        if (!active) return;
        setAppUsers(loadedUsers.length ? loadedUsers : fallbackUsers);
      })
      .catch(() => {
        if (!active) return;
        if (apiMode === "real") {
          setErrorMessage(API_UNAVAILABLE_MESSAGE);
        }
        setAppUsers(fallbackUsers);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setErrorMessage(null);
    fetchDashboardData(selectedUserId)
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
        setErrorMessage(apiMode === "real" ? API_UNAVAILABLE_MESSAGE : "Mock data could not be loaded.");
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [selectedUserId]);

  const selectedUser = appUsers.find((user) => user.id === selectedUserId) ?? fallbackUsers[0];
  const userJobs = useMemo(() => jobs.filter((job) => job.userId === selectedUserId), [jobs, selectedUserId]);
  const latestRun = runs
    .filter((run) => run.userId === selectedUserId)
    .sort((a, b) => b.startedAt.localeCompare(a.startedAt))[0];

  async function refreshSelectedUserData() {
    setLoading(true);
    setErrorMessage(null);
    try {
      const [loadedJobs, loadedRuns, loadedOverview, loadedPreference, loadedDocuments, loadedSources] =
        await fetchDashboardData(selectedUserId);
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
      setErrorMessage(apiMode === "real" ? API_UNAVAILABLE_MESSAGE : "Mock data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  async function updateStatus(jobId: number, status: JobStatus) {
    setErrorMessage(null);
    try {
      await client.updateJobStatus(selectedUserId, jobId, status);
      setJobs((current) => current.map((job) => (job.id === jobId ? { ...job, status } : job)));
      setOverview((current) => {
        if (!current) return current;
        return {
          ...current,
          topRecommendedJobs: current.topRecommendedJobs.map((job) => (job.id === jobId ? { ...job, status } : job)),
        };
      });
    } catch {
      setErrorMessage(apiMode === "real" ? "Status update failed. Check the local API server and database connection." : "Status update failed.");
    }
  }

  function loadJobDetail(jobId: number): Promise<Job> {
    return client.getJob(selectedUserId, jobId);
  }

  function prepareAnalysisRequest(): Promise<AnalysisRequestResult> {
    return client.prepareAnalysisRequest(selectedUserId);
  }

  async function importAnalysisResult(resultPath: string, overwrite: boolean): Promise<AnalysisImportResult> {
    const result = await client.importAnalysisResult(resultPath, overwrite);
    await refreshSelectedUserData();
    return result;
  }

  return (
    <AppShell
      onNavigate={setPage}
      onRefreshData={refreshSelectedUserData}
      onUserChange={setSelectedUserId}
      page={page}
      selectedUserId={selectedUserId}
      users={appUsers}
    >
      <div className="px-margin_mobile pt-3 md:px-margin_desktop">
        <div className="flex flex-wrap items-center gap-2 font-label-sm text-label-sm text-on-surface-variant">
          <span className="rounded-full bg-surface-container-low px-2 py-1">Data mode: {apiMode}</span>
          {loading ? <span className="rounded-full bg-surface-container-low px-2 py-1">Loading...</span> : null}
        </div>
        {errorMessage ? (
          <div className="mt-3 rounded-lg border border-error-container bg-surface-container-lowest px-4 py-3 font-body-md text-body-md text-on-error-container">
            {errorMessage}
          </div>
        ) : null}
      </div>
      {page === "overview" ? (
        <OverviewPage jobs={userJobs} latestRun={latestRun} onViewJobs={() => setPage("jobs")} overview={overview} user={selectedUser} />
      ) : null}
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
      {page === "settings" ? (
        <SettingsPage dataSources={sourceStatuses} documents={userDocuments} preferences={userPreference} user={selectedUser} />
      ) : null}
    </AppShell>
  );
}
