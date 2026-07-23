import "server-only";

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

export type MarketRow = {
  id: string;
  name: string;
  history_data: string;
  order: number;
  updated_at: string | null;
};

export type MarketSummary = {
  id: string;
  name: string;
  order: number;
  source: "Primary" | "Rajapaito";
  latestResult: string | null;
  historyCount: number;
  updatedAt: string | null;
  isStale: boolean;
};

export type DashboardData = {
  markets: MarketSummary[];
  totalMarkets: number;
  fullHistoryMarkets: number;
  staleMarkets: number;
  latestUpdate: string | null;
};

let client: SupabaseClient | null = null;

function requiredEnvironment(name: "SUPABASE_URL" | "SUPABASE_SERVICE_ROLE_KEY"): string {
  const value = process.env[name]?.trim();
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function staleThresholdHours(): number {
  const raw = Number(process.env.DASHBOARD_STALE_HOURS ?? "8");
  return Number.isFinite(raw) && raw > 0 ? raw : 8;
}

export function getSupabaseAdmin(): SupabaseClient {
  if (!client) {
    client = createClient(
      requiredEnvironment("SUPABASE_URL"),
      requiredEnvironment("SUPABASE_SERVICE_ROLE_KEY"),
      {
        auth: {
          autoRefreshToken: false,
          persistSession: false,
        },
      },
    );
  }
  return client;
}

function summarizeMarket(row: MarketRow, now: number): MarketSummary {
  const history = String(row.history_data ?? "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  const updatedTimestamp = row.updated_at ? Date.parse(row.updated_at) : Number.NaN;
  const staleAfterMs = staleThresholdHours() * 60 * 60 * 1000;

  return {
    id: String(row.id),
    name: String(row.name || row.id),
    order: Number(row.order ?? 0),
    source: Number(row.order ?? 0) >= 59 ? "Rajapaito" : "Primary",
    latestResult: history.at(-1) ?? null,
    historyCount: history.length,
    updatedAt: row.updated_at,
    isStale:
      !Number.isFinite(updatedTimestamp) || now - updatedTimestamp > staleAfterMs,
  };
}

export async function getDashboardData(): Promise<DashboardData> {
  const { data, error } = await getSupabaseAdmin()
    .from("markets")
    .select("id,name,history_data,order,updated_at")
    .order("order", { ascending: true });

  if (error) {
    throw new Error(`Unable to load markets: ${error.message}`);
  }

  const now = Date.now();
  const markets = ((data ?? []) as MarketRow[]).map((row) => summarizeMarket(row, now));
  const latestUpdate = markets
    .map((market) => market.updatedAt)
    .filter((value): value is string => Boolean(value))
    .sort()
    .at(-1) ?? null;

  return {
    markets,
    totalMarkets: markets.length,
    fullHistoryMarkets: markets.filter((market) => market.historyCount >= 1200).length,
    staleMarkets: markets.filter((market) => market.isStale).length,
    latestUpdate,
  };
}

export async function getMarketById(marketId: string): Promise<MarketRow | null> {
  const { data, error } = await getSupabaseAdmin()
    .from("markets")
    .select("id,name,history_data,order,updated_at")
    .eq("id", marketId)
    .maybeSingle();

  if (error) {
    throw new Error(`Unable to load market ${marketId}: ${error.message}`);
  }

  return (data as MarketRow | null) ?? null;
}
