import { NextResponse } from "next/server";

import { getDashboardData } from "@/lib/markets";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const dashboard = await getDashboardData();
    const healthy = dashboard.totalMarkets > 0 && dashboard.staleMarkets === 0;
    return NextResponse.json(
      {
        status: healthy ? "ok" : "degraded",
        service: "new-engine-web",
        total_markets: dashboard.totalMarkets,
        stale_markets: dashboard.staleMarkets,
        latest_update: dashboard.latestUpdate,
        engine_release: "research_only",
      },
      { status: healthy ? 200 : 503 },
    );
  } catch (error) {
    return NextResponse.json(
      {
        status: "error",
        service: "new-engine-web",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    );
  }
}
