import Link from "next/link";
import { notFound } from "next/navigation";

import { getMarketById } from "@/lib/markets";

export const dynamic = "force-dynamic";

type PositionStat = {
  label: string;
  ranking: Array<{ digit: number; count: number; rate: number }>;
};

function formatTimestamp(value: string | null): string {
  if (!value) return "Belum ada";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Invalid";
  return new Intl.DateTimeFormat("id-ID", {
    timeZone: "Asia/Makassar",
    dateStyle: "medium",
    timeStyle: "medium",
    hour12: false,
  }).format(date);
}

function positionStatistics(history: string[]): PositionStat[] {
  const labels = ["AS", "KOP", "KEPALA", "EKOR"];
  return labels.map((label, position) => {
    const counts = Array.from({ length: 10 }, () => 0);
    for (const result of history) {
      const digit = Number(result[position]);
      if (Number.isInteger(digit) && digit >= 0 && digit <= 9) counts[digit] += 1;
    }
    const ranking = counts
      .map((count, digit) => ({
        digit,
        count,
        rate: history.length ? count / history.length : 0,
      }))
      .sort((left, right) => right.count - left.count || left.digit - right.digit)
      .slice(0, 5);
    return { label, ranking };
  });
}

export default async function MarketDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const marketId = decodeURIComponent(id);
  const market = await getMarketById(marketId);

  if (!market) notFound();

  const history = market.history_data.trim().split(/\s+/).filter(Boolean);
  const recent = history.slice(-120).reverse();
  const stats = positionStatistics(history);
  const source = market.order >= 59 ? "Rajapaito" : "Primary";

  return (
    <main className="shell detail-shell">
      <header className="topbar">
        <Link className="brand-block brand-link" href="/">
          <div className="brand-mark" aria-hidden="true">NE</div>
          <div>
            <p className="brand-name">NEW.ENGINE</p>
            <p className="brand-subtitle">Research Console</p>
          </div>
        </Link>
        <div className="topbar-status">
          <Link className="back-link" href="/">Data registry</Link>
          <Link
            className="status-pill status-research"
            href={`/engine/markets/${encodeURIComponent(market.id)}`}
          >
            ENGINE AUDIT
          </Link>
        </div>
      </header>

      <section className="detail-hero panel">
        <div>
          <p className="eyebrow">MARKET / {source.toUpperCase()}</p>
          <h1>{market.name}</h1>
          <p className="mono dim">{market.id}</p>
        </div>
        <div className="detail-result">
          <span>Latest result</span>
          <strong className="mono">{history.at(-1) ?? "—"}</strong>
        </div>
      </section>

      <section className="metric-grid detail-metrics">
        <article className="metric-card">
          <p>History depth</p>
          <strong>{history.length.toLocaleString("id-ID")}</strong>
          <span>result tersimpan</span>
        </article>
        <article className="metric-card">
          <p>Registry order</p>
          <strong>{market.order}</strong>
          <span>{source}</span>
        </article>
        <article className="metric-card wide-metric">
          <p>Last update</p>
          <strong className="timestamp-value">{formatTimestamp(market.updated_at)}</strong>
          <span>Asia/Makassar</span>
        </article>
      </section>

      <section className="panel stats-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">DESCRIPTIVE DISTRIBUTION</p>
            <h2>Top digit frequency by position</h2>
            <p className="muted">Statistik deskriptif seluruh histori, bukan output prediksi.</p>
          </div>
          <span className="status-pill status-research">RESEARCH ONLY</span>
        </div>
        <div className="position-grid">
          {stats.map((stat) => (
            <article className="position-card" key={stat.label}>
              <div className="position-title">
                <strong>{stat.label}</strong>
                <span>Top 5</span>
              </div>
              <div className="digit-bars">
                {stat.ranking.map((item) => (
                  <div className="digit-bar-row" key={item.digit}>
                    <span className="digit-badge mono">{item.digit}</span>
                    <div className="bar-track">
                      <i style={{ width: `${Math.max(4, item.rate * 100)}%` }} />
                    </div>
                    <span className="mono small">{(item.rate * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="panel history-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">RECENT HISTORY</p>
            <h2>120 result terbaru</h2>
            <p className="muted">Ditampilkan terbaru → terlama. Penyimpanan database tetap lama → terbaru.</p>
          </div>
        </div>
        <div className="result-grid">
          {recent.map((result, index) => (
            <div className="result-token mono" key={`${result}-${index}`}>
              <span>{result}</span>
              <small>-{index}</small>
            </div>
          ))}
        </div>
      </section>

      <footer>
        <span>{market.name}</span>
        <span className="mono">SNAPSHOT AUDIT VIEW</span>
      </footer>
    </main>
  );
}
