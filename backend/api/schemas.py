from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


UserId = Literal["minjian", "chang"]
JobStatus = Literal["new", "saved", "applied", "ignored"]
Discovery = Literal["new_in_this_run", "seen_before", "historical"]
Source = Literal["LinkedIn", "StepStone", "Indeed"]
Priority = Literal["High", "Medium", "Low", "Not analyzed"]


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class UserResponse(ApiModel):
    id: str
    displayName: str


class CodexJobAnalysisResponse(ApiModel):
    score: float | None
    priority: str
    reason: str
    concern: str
    suggestedStatus: str | None = None
    analyzedAt: str | None = None
    analysisBatchId: int | None = None


class JobResponse(ApiModel):
    id: int
    userId: str
    title: str
    company: str
    location: str
    source: str
    url: str
    shortDescription: str
    likelyRelevant: bool
    matchedKeywords: list[str]
    matchedLocations: list[str]
    exclusionMatches: list[str]
    status: str
    discovery: str
    firstSeenAt: str
    lastSeenAt: str
    lastSeenRunId: int | None = None
    codexAnalysis: CodexJobAnalysisResponse | None = None


class UserJobStatusUpdate(ApiModel):
    userId: str
    status: JobStatus


class UserJobStatusResponse(ApiModel):
    userId: str
    jobId: int
    status: JobStatus


class IngestionRunResponse(ApiModel):
    id: int
    userId: str
    startedAt: str
    completedAt: str
    emailsFetched: int
    jobsParsed: int
    newlyDiscovered: int
    seenAgain: int
    duplicatesSkipped: int
    likelyRelevant: int
    codexAnalyzed: int


class OverviewResponse(ApiModel):
    userId: str
    range: str
    metrics: dict[str, int]
    latestRun: IngestionRunResponse | None
    sourceSummary: dict[str, int]
    topRecommendedJobs: list[JobResponse]
    recentActivity: list[dict[str, str]]


class AnalysisRequestCreate(ApiModel):
    userId: str
    limit: int = 20
    status: JobStatus | None = None
    latestRun: bool = True
    runId: int | None = None
    sinceDays: int | None = None
    newInRunOnly: bool = False
    likelyRelevantOnly: bool = False
    notAnalyzedOnly: bool = False


class AnalysisRequestResponse(ApiModel):
    analysisBatchId: int
    userId: str
    jobCount: int
    requestMarkdownPath: str
    requestJsonPath: str
    message: str


class AnalysisImportCreate(ApiModel):
    resultPath: str
    overwrite: bool = False


class AnalysisImportResponse(ApiModel):
    importedCount: int
    skippedCount: int
    updatedStatusesCount: int
    resultPath: str
    message: str
