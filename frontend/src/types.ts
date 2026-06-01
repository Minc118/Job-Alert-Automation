export type UserId = string;
export type JobStatus = "new" | "saved" | "applied" | "ignored";
export type Discovery = "new_in_this_run" | "seen_before" | "historical";
export type Source = "LinkedIn" | "StepStone" | "Indeed";
export type Priority = "High" | "Medium" | "Low" | "Not analyzed";

export interface User {
  id: UserId;
  displayName: string;
}

export interface JobAnalysis {
  score: number | null;
  priority: Priority;
  reason: string;
  concern: string;
  suggestedStatus?: JobStatus;
  analyzedAt?: string;
  analysisBatchId?: number;
}

export interface Job {
  id: number;
  userId: UserId;
  title: string;
  company: string;
  location: string;
  source: Source;
  url: string;
  shortDescription: string;
  likelyRelevant: boolean;
  matchedKeywords: string[];
  matchedLocations: string[];
  exclusionMatches: string[];
  status: JobStatus;
  discovery: Discovery;
  firstSeenAt: string;
  lastSeenAt: string;
  lastSeenRunId?: number;
  codexAnalysis?: JobAnalysis;
  gptPrompt: string;
}

export interface IngestionRun {
  id: number;
  userId: UserId;
  startedAt: string;
  completedAt: string;
  emailsFetched: number;
  jobsParsed: number;
  newlyDiscovered: number;
  seenAgain: number;
  duplicatesSkipped: number;
  likelyRelevant: number;
  codexAnalyzed: number;
}

export interface UserPreferences {
  userId: UserId;
  targetRoleKeywords: string[];
  preferredLocations: string[];
  excludedKeywords: string[];
  sourceQueries: Record<string, string>;
}

export interface UserDocument {
  id: number;
  userId: UserId;
  documentType: "profile_markdown" | "resume_pdf" | "cover_letter_template";
  originalFilename: string;
  storedPath: string;
  status: "connected" | "missing";
  isActive: boolean;
  createdAt?: string;
}

export interface DataSourceStatus {
  source: Source;
  status: "active" | "disconnected";
  lastSeenAt?: string;
}

export interface OverviewData {
  userId: UserId;
  range: string;
  metrics: {
    newJobs: number;
    newlyDiscovered: number;
    likelyRelevant: number;
    codexHighPriority: number;
    saved: number;
    applied: number;
    ignored: number;
  };
  latestRun: IngestionRun | null;
  sourceSummary: Partial<Record<Source, number>>;
  topRecommendedJobs: Job[];
  recentActivity: Array<{ label: string; time: string }>;
}

export interface AnalysisRequestResult {
  analysisBatchId: number;
  userId: UserId;
  jobCount: number;
  requestMarkdownPath: string;
  requestJsonPath: string;
  message: string;
}

export interface AnalysisImportResult {
  importedCount: number;
  skippedCount: number;
  updatedStatusesCount: number;
  resultPath: string;
  message: string;
}

export interface AiAnalysisRunResult {
  analysis_batch_id: number;
  provider: string;
  model: string;
  requested_job_count: number;
  analyzed_count: number;
  skipped_count: number;
  failed_count: number;
  results: Array<{
    job_id: number;
    score: number | null;
    priority: Priority;
    suggested_status: JobStatus | null;
  }>;
  warnings: string[];
}

export type Page = "overview" | "jobs" | "settings";
