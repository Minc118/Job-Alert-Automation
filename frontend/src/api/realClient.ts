import { dataSources, documents, preferences } from "../data/mockData";
import type { AnalysisImportResult, AnalysisRequestResult, DataSourceStatus, IngestionRun, Job, OverviewData, User, UserDocument, UserId, UserPreferences } from "../types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/api${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function patchJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/api${path}`, {
    method: "PATCH",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/api${path}`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

function normalizeJob(job: Job): Job {
  return {
    ...job,
    company: job.company || "",
    location: job.location || "",
    url: job.url || "",
    shortDescription: job.shortDescription || "",
    matchedKeywords: job.matchedKeywords ?? [],
    matchedLocations: job.matchedLocations ?? [],
    exclusionMatches: job.exclusionMatches ?? [],
    gptPrompt:
      job.gptPrompt ||
      `Draft a concise application prompt for the '${job.title}' role at ${job.company || "the company"}. Use the local private profile and do not invent missing requirements.`,
  };
}

export const realClient = {
  getUsers(): Promise<User[]> {
    return getJson<User[]>("/users");
  },
  async getOverview(userId: UserId, range = "latest_run"): Promise<OverviewData> {
    const overview = await getJson<OverviewData>(`/overview?user_id=${encodeURIComponent(userId)}&range=${encodeURIComponent(range)}`);
    return {
      ...overview,
      topRecommendedJobs: overview.topRecommendedJobs.map(normalizeJob),
    };
  },
  async getJobs(userId: UserId, range = "latest_run"): Promise<Job[]> {
    const jobs = await getJson<Job[]>(`/jobs?user_id=${encodeURIComponent(userId)}&range=${encodeURIComponent(range)}`);
    return jobs.map(normalizeJob);
  },
  async getJob(userId: UserId, jobId: number): Promise<Job> {
    const job = await getJson<Job>(`/jobs/${jobId}?user_id=${encodeURIComponent(userId)}`);
    return normalizeJob(job);
  },
  getRuns(userId: UserId): Promise<IngestionRun[]> {
    return getJson<IngestionRun[]>(`/runs?user_id=${encodeURIComponent(userId)}`);
  },
  async getPreferences(userId: UserId): Promise<UserPreferences> {
    return preferences.find((item) => item.userId === userId)!;
  },
  async getDocuments(userId: UserId): Promise<UserDocument[]> {
    return documents.filter((document) => document.userId === userId);
  },
  async getDataSources(): Promise<DataSourceStatus[]> {
    return dataSources;
  },
  updateJobStatus(userId: UserId, jobId: number, status: Job["status"]): Promise<{ userId: string; jobId: number; status: Job["status"] }> {
    return patchJson(`/user-jobs/${jobId}/status`, { userId, status });
  },
  prepareAnalysisRequest(userId: UserId): Promise<AnalysisRequestResult> {
    return postJson("/analysis-requests", {
      userId,
      limit: 20,
      latestRun: true,
      newInRunOnly: true,
      likelyRelevantOnly: false,
      notAnalyzedOnly: false,
    });
  },
  importAnalysisResult(resultPath: string, overwrite = false): Promise<AnalysisImportResult> {
    return postJson("/analysis-import", { resultPath, overwrite });
  },
};
