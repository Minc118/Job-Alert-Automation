import type { AnalysisImportResult, AnalysisRequestResult, DataSourceStatus, IngestionRun, Job, OverviewData, User, UserDocument, UserId, UserPreferences } from "../types";
import { mockClient } from "./mockClient";
import { realClient } from "./realClient";

export interface DashboardClient {
  getUsers(): Promise<User[]>;
  getOverview(userId: UserId, range?: string): Promise<OverviewData>;
  getJobs(userId: UserId, range?: string): Promise<Job[]>;
  getJob(userId: UserId, jobId: number): Promise<Job>;
  getRuns(userId: UserId): Promise<IngestionRun[]>;
  getPreferences(userId: UserId): Promise<UserPreferences>;
  getDocuments(userId: UserId): Promise<UserDocument[]>;
  getDataSources(): Promise<DataSourceStatus[]>;
  updateJobStatus(userId: UserId, jobId: number, status: Job["status"]): Promise<{ userId: string; jobId: number; status: Job["status"] }>;
  prepareAnalysisRequest(userId: UserId): Promise<AnalysisRequestResult>;
  importAnalysisResult(resultPath: string, overwrite?: boolean): Promise<AnalysisImportResult>;
}

export const apiMode = import.meta.env.VITE_API_MODE === "real" ? "real" : "mock";
export const client: DashboardClient = apiMode === "real" ? realClient : mockClient;
