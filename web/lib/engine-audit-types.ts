export type EngineRunStatus = "running" | "succeeded" | "partial" | "failed";

export type SelectedCandidate = {
  modelName: string;
  position: number;
  window: number;
  horizon: number;
  sampleSize: number;
  topK: number;
  hits: number;
  hitRate: number;
  baselineHitRate: number;
  lift: number;
  recentHitRate: number;
  longestMissStreak: number;
  meanActualProbability: number;
  logLoss: number;
  brierScore: number;
};

export type AuditPosition = {
  position: number;
  selectedCandidate: SelectedCandidate;
  rankedDigits: number[];
  topDigits: number[];
  probabilities: Record<string, number>;
};

export type EngineRun = {
  id: string;
  engineVersion: string;
  releaseStatus: string;
  status: EngineRunStatus;
  source: string;
  startedAt: string;
  finishedAt: string | null;
  marketsLoaded: number;
  marketsEvaluated: number;
  validationErrorCount: number;
  engineErrorCount: number;
  config: Record<string, unknown>;
};

export type EngineMarketAudit = {
  runId: string;
  marketId: string;
  marketName: string;
  generatedAt: string;
  historySize: number;
  historyUpdatedAt: string | null;
  candidateCount: number;
  releaseStatus: string;
  positions: AuditPosition[];
};
