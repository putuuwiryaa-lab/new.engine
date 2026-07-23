import "server-only";

import { getSupabaseAdmin } from "@/lib/markets";

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

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function asNullableString(value: unknown): string | null {
  return typeof value === "string" && value ? value : null;
}

function asNumber(value: unknown, fallback = 0): number {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function asNumberArray(value: unknown): number[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => asNumber(item, Number.NaN))
    .filter((item) => Number.isFinite(item));
}

function parseStatus(value: unknown): EngineRunStatus {
  return value === "running" || value === "succeeded" || value === "partial" || value === "failed"
    ? value
    : "failed";
}

function parseCandidate(value: unknown): SelectedCandidate {
  const record = asRecord(value);
  return {
    modelName: asString(record.model_name, "unknown"),
    position: asNumber(record.position),
    window: asNumber(record.window),
    horizon: asNumber(record.horizon),
    sampleSize: asNumber(record.sample_size),
    topK: asNumber(record.top_k),
    hits: asNumber(record.hits),
    hitRate: asNumber(record.hit_rate),
    baselineHitRate: asNumber(record.baseline_hit_rate),
    lift: asNumber(record.lift),
    recentHitRate: asNumber(record.recent_hit_rate),
    longestMissStreak: asNumber(record.longest_miss_streak),
    meanActualProbability: asNumber(record.mean_actual_probability),
    logLoss: asNumber(record.log_loss),
    brierScore: asNumber(record.brier_score),
  };
}

function parsePosition(value: unknown): AuditPosition {
  const record = asRecord(value);
  const rawProbabilities = asRecord(record.probabilities);
  const probabilities = Object.fromEntries(
    Object.entries(rawProbabilities).map(([digit, probability]) => [digit, asNumber(probability)]),
  );

  return {
    position: asNumber(record.position),
    selectedCandidate: parseCandidate(record.selected_candidate),
    rankedDigits: asNumberArray(record.ranked_digits),
    topDigits: asNumberArray(record.top_digits),
    probabilities,
  };
}

function parseRun(row: Record<string, unknown>): EngineRun {
  return {
    id: asString(row.id),
    engineVersion: asString(row.engine_version),
    releaseStatus: asString(row.release_status, "research_only"),
    status: parseStatus(row.status),
    source: asString(row.source, "unknown"),
    startedAt: asString(row.started_at),
    finishedAt: asNullableString(row.finished_at),
    marketsLoaded: asNumber(row.markets_loaded),
    marketsEvaluated: asNumber(row.markets_evaluated),
    validationErrorCount: asNumber(row.validation_error_count),
    engineErrorCount: asNumber(row.engine_error_count),
    config: asRecord(row.config),
  };
}

function parseAudit(row: Record<string, unknown>): EngineMarketAudit {
  const payload = asRecord(row.audit);
  const rawPositions = Array.isArray(payload.positions) ? payload.positions : [];

  return {
    runId: asString(row.run_id),
    marketId: asString(row.market_id),
    marketName: asString(row.market_name, asString(row.market_id)),
    generatedAt: asString(row.generated_at),
    historySize: asNumber(row.history_size),
    historyUpdatedAt: asNullableString(row.history_updated_at),
    candidateCount: asNumber(row.candidate_count),
    releaseStatus: asString(row.release_status, "research_only"),
    positions: rawPositions.map(parsePosition).sort((left, right) => left.position - right.position),
  };
}

export async function getLatestEngineRun(): Promise<EngineRun | null> {
  const { data, error } = await getSupabaseAdmin()
    .from("engine_runs")
    .select(
      "id,engine_version,release_status,status,source,started_at,finished_at,markets_loaded,markets_evaluated,validation_error_count,engine_error_count,config",
    )
    .order("started_at", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) throw new Error(`Unable to load latest engine run: ${error.message}`);
  return data ? parseRun(data as Record<string, unknown>) : null;
}

export async function getEngineRunAudits(runId: string): Promise<EngineMarketAudit[]> {
  const { data, error } = await getSupabaseAdmin()
    .from("engine_market_audits")
    .select(
      "run_id,market_id,market_name,generated_at,history_size,history_updated_at,candidate_count,release_status,audit",
    )
    .eq("run_id", runId)
    .order("market_name", { ascending: true });

  if (error) throw new Error(`Unable to load engine audits: ${error.message}`);
  return ((data ?? []) as Record<string, unknown>[]).map(parseAudit);
}

export async function getLatestMarketAudit(marketId: string): Promise<EngineMarketAudit | null> {
  const { data, error } = await getSupabaseAdmin()
    .from("engine_market_audits")
    .select(
      "run_id,market_id,market_name,generated_at,history_size,history_updated_at,candidate_count,release_status,audit",
    )
    .eq("market_id", marketId)
    .order("generated_at", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) throw new Error(`Unable to load market audit ${marketId}: ${error.message}`);
  return data ? parseAudit(data as Record<string, unknown>) : null;
}
