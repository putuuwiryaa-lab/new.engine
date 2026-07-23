import Link from "next/link";

import { MarketTable } from "@/components/market-table";
import { getDashboardData } from "@/lib/markets";

export const dynamic = "force-dynamic";

function formatTimestamp(value: string | null): string {
  if (!value) return "Belum ada data";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Timestamp invalid";
  return new Intl.DateTimeFormat("id-ID", {
    timeZone: "Asia/Makassar",
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date);
}

function SetupError({ message }: { message: string }) {
  return (
    <main className="shell centered-shell">
      <section className="panel setup-error">
        <p className="eyebrow">CONFIGURATION REQUIRED</p>
        <h1>Dashboard belum dapat membaca Supabase.</h1>
        <p>{message}</p>
        <div className="code-card mono">
          SUPABASE_URL<br />
          SUPABASE_SERVICE_ROLE_KEY
        </div>
        <p className="muted">Tambahkan kedua environment variable tersebut pada project Vercel.</p>
      </section>
    </main>
  );
}

export default async function DashboardPage() {
  let dashboard;
  try {
    dashboard = await getDashboardData();
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown data access error";
    return <SetupError message={message} />;
  }

  const freshnessLabel = dashboard.staleMarkets === 0 ? "NOMINAL" : "ATTENTION";

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark" aria-hidden="true">NE</div>
          <div>
            <p className="brand-name">NEW.ENGINE</p>
            <p className="brand-subtitle">Adaptive Probability Intelligence</p>
          </div>
        </div>
        <div className="topbar-status">
          <span className="status-pill status-ok"><span className="status-dot" />PIPELINE ONLINE</span>
          <Link className="status-pill status-research" href="/engine">EVIDENCE GATE</Link>
        </div>
      </header>

      <section className="hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">RESEARCH CONSOLE / DATA FIRST</p>
          <h1>Market data integrity before model release.</h1>
          <p>
            Console operasional untuk memeriksa freshness, kedalaman histori, snapshot terbaru,
            audit probabilitas, dan evidence gate sebelum kandidat mendapat izin rilis.
          </p>
          <div className="hero-meta">
            <span>Last ingest</span>
            <strong className="mono">{formatTimestamp(dashboard.latestUpdate)} WITA</strong>
          </div>
        </div>

        <aside className="release-card">
          <div className="release-card-top">
            <p className="eyebrow">PRODUCTION RELEASE</p>
            <span className="status-pill status-research">RESEARCH ONLY</span>
          </div>
          <div className="release-lock">LOCKED</div>
          <p>
            Full engine audit dan deterministic evidence gate sudah aktif. Gate pass belum berarti
            prediksi produksi; prediction journal dan automatic settlement tetap wajib sebelum rilis.
          </p>
          <div className="release-lines">
            <span><i />Walk-forward evaluation</span>
            <span><i />Baseline comparison</span>
            <span><i />Audit persistence</span>
            <span><i />Evidence release gate</span>
            <span className="pending"><i />Prediction journal</span>
          </div>
          <div style={{ marginTop: 22 }}>
            <Link className="status-pill status-research" href="/engine">BUKA EVIDENCE GATE →</Link>
          </div>
        </aside>
      </section>

      <section className="metric-grid" aria-label="Pipeline metrics">
        <article className="metric-card">
          <p>Total market</p>
          <strong>{dashboard.totalMarkets}</strong>
          <span>Registry aktif</span>
        </article>
        <article className="metric-card">
          <p>Full history</p>
          <strong>{dashboard.fullHistoryMarkets}</strong>
          <span>≥ 1.200 result</span>
        </article>
        <article className="metric-card">
          <p>Stale market</p>
          <strong className={dashboard.staleMarkets ? "metric-warning" : ""}>{dashboard.staleMarkets}</strong>
          <span>Threshold 8 jam</span>
        </article>
        <article className="metric-card accent-card">
          <p>Data state</p>
          <strong className="state-label">{freshnessLabel}</strong>
          <span>{dashboard.staleMarkets ? "Perlu investigasi" : "Siap untuk audit"}</span>
        </article>
      </section>

      <section className="pipeline-strip panel">
        <div className="pipeline-step complete">
          <span>01</span>
          <div><strong>Scraper</strong><small>Render / 6 jam</small></div>
        </div>
        <div className="pipeline-line" />
        <div className="pipeline-step complete">
          <span>02</span>
          <div><strong>Validation</strong><small>Guard + retry</small></div>
        </div>
        <div className="pipeline-line" />
        <div className="pipeline-step complete">
          <span>03</span>
          <div><strong>Engine Audit</strong><small>71 market persisted</small></div>
        </div>
        <div className="pipeline-line" />
        <div className="pipeline-step complete">
          <span>04</span>
          <div><strong>Evidence Gate</strong><small>PASS / HOLD checks</small></div>
        </div>
      </section>

      <MarketTable markets={dashboard.markets} />

      <footer>
        <span>NEW.ENGINE Research Console</span>
        <span className="mono">DATA FIRST · EVIDENCE BEFORE UPGRADE · AUDITABLE</span>
      </footer>
    </main>
  );
}
