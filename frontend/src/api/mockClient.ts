import { dataSources, documents, ingestionRuns, jobs, preferences, users } from "../data/mockData";
import type { AnalysisImportResult, AnalysisRequestResult, DataSourceStatus, IngestionRun, Job, OverviewData, User, UserDocument, UserId, UserPreferences } from "../types";

function getLatestRun(userId: UserId): IngestionRun | null {
  return (
    ingestionRuns
      .filter((run) => run.userId === userId)
      .sort((a, b) => b.startedAt.localeCompare(a.startedAt))[0] ?? null
  );
}

export const mockClient = {
  async getUsers(): Promise<User[]> {
    return users;
  },
  async getOverview(userId: UserId): Promise<OverviewData> {
    const userJobs = jobs.filter((job) => job.userId === userId);
    const sourceSummary = userJobs.reduce<OverviewData["sourceSummary"]>((acc, job) => {
      acc[job.source] = (acc[job.source] ?? 0) + 1;
      return acc;
    }, {});
    return {
      userId,
      range: "latest_run",
      metrics: {
        newJobs: userJobs.filter((job) => job.status === "new").length,
        newlyDiscovered: userJobs.filter((job) => job.discovery === "new_in_this_run").length,
        likelyRelevant: userJobs.filter((job) => job.likelyRelevant).length,
        codexHighPriority: userJobs.filter((job) => job.codexAnalysis?.priority === "High").length,
        saved: userJobs.filter((job) => job.status === "saved").length,
        applied: userJobs.filter((job) => job.status === "applied").length,
        ignored: userJobs.filter((job) => job.status === "ignored").length,
      },
      latestRun: getLatestRun(userId),
      sourceSummary,
      topRecommendedJobs: userJobs
        .filter((job) => job.codexAnalysis?.priority === "High" || job.codexAnalysis?.priority === "Medium")
        .sort((a, b) => (b.codexAnalysis?.score ?? 0) - (a.codexAnalysis?.score ?? 0))
        .slice(0, 5),
      recentActivity: [
        { label: "Latest analysis import", time: "Today, 10:05" },
        { label: "Latest job fetch completed", time: "Today, 09:32" },
      ],
    };
  },
  async getJobs(userId: UserId): Promise<Job[]> {
    return jobs.filter((job) => job.userId === userId);
  },
  async getJob(userId: UserId, jobId: number): Promise<Job> {
    const job = jobs.find((item) => item.userId === userId && item.id === jobId);
    if (!job) {
      throw new Error("Job not found");
    }
    return job;
  },
  async getRuns(userId: UserId): Promise<IngestionRun[]> {
    return ingestionRuns.filter((run) => run.userId === userId);
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
  async updateJobStatus(userId: UserId, jobId: number, status: Job["status"]): Promise<{ userId: string; jobId: number; status: Job["status"] }> {
    return { userId, jobId, status };
  },
  async prepareAnalysisRequest(userId: UserId): Promise<AnalysisRequestResult> {
    return {
      analysisBatchId: 0,
      userId,
      jobCount: jobs.filter((job) => job.userId === userId && job.status === "new").length,
      requestMarkdownPath: `output/analysis_requests/latest_${userId}.md`,
      requestJsonPath: `output/analysis_requests/latest_${userId}.json`,
      message: "Mock analysis request prepared. No files were written in mock mode.",
    };
  },
  async importAnalysisResult(resultPath: string): Promise<AnalysisImportResult> {
    return {
      importedCount: 0,
      skippedCount: 0,
      updatedStatusesCount: 0,
      resultPath,
      message: "Mock analysis result import completed. No database rows were changed in mock mode.",
    };
  },
};
