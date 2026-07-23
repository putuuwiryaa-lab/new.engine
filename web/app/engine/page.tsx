import Link from "next/link";

import { EngineAuditList } from "@/components/engine-audit-list";
import { getEngineRunAudits, getLatestEngineRun } from "@/lib/engine-audits";

import styles from "./engine.module.css";

export const dynamic = "force-dynamic";

function formatTimestamp(value: string | null): string {
  if (!value) return "Belum selesai";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Timestamp invalid";
  return new Intl.DateTimeFormat("id-ID", {
    timeZone: "Asia/Makassar",
    dateStyle: "medium",
    timeStyle: "medium",
    hour12: false,
  }).format(date);
}

function formatDuration(startedAt: string, finishedAt: string | null): string {
  if (!finishedAt) return "RUNNING";
  const started = Date.parse(startedAt);
  const finished = Date.parse(finishedAt);
  if (!Number.isFinite(started) || !Number.isFinite(finished) || finished < started) return "Invalid";
  const totalSeconds = Math.round((finished - started) / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}m ${seconds}s`;
}

function statusClass(status: string): string {
  if (status === "succeeded") return "status-ok";
  if (status === "running") return "status-research";
  return "status-warn";
}

function configValue(value: unknown): string {
  if (Array.isArray(value)) return value.join(",");
  if (value === null || value === undefined) return "—";
  return String(value);
}

function SetupError({ message }: { message: string }) {
  return (
    <main className="shell centered-shell">
      <section className="panel setup-error">
        <p className="eyebrow">ENGINE AUDIT UNAVAILABLE</p>
        <h1>Audit engine belum dapat dibaca.</h1>
        <p>{message}</p>
        <p className="muted">Pastikan tabel persistence sudah dibuat dan full pipeline pernah dijalankan.</p>
      </section>
    </main>
  );
}

export default async function EnginePage() {
  let run;
  let audits;

  try {
    run = await getLatestEngineRun();
    audits = run ? await getEngineRunAudits(run.id) : [];
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown engine audit error";
    return <SetupError message={message} />;
  }

  if (!run) {
    return (
      <main className={`shell ${styles.shell}`}>
        <header className="topbar">
          <Link className="brand-block brand-link" href="/">
            <div className="brand-mark" aria-hidden="true">NE</div>
            <div>
              <p className="brand-name">NEW.ENGINE</p>
              <p className="brand-subtitle">Engine Audit Console</p>
            </div>
          </Link>
          <Link className={styles.navLink} href="/">Data registry</Link>
        </header>
        <section className={`panel ${styles.emptyPanel}`}>
          <p className="eyebrow">NO ENGINE RUN</p>
          <h2>Belum ada audit tersimpan.</h2>
          <p className="muted">Jalankan full pipeline Render sekali. Halaman ini akan membaca run terbaru secara otomatis.</p>
        </section>
      </main>
    );
  }

  const allPositiveMarkets = audits.filter((audit) =>
    audit.positions.length === 4 && audit.positions.every((position) => position.selectedCandidate.lift > 0),
  ).length;
  const configuration = run.config;

  return (
    <main className={`shell ${styles.shell}`}>
      <header className="topbar">
        <Link className="brand-block brand-link" href="/">
          <div className="brand-mark" aria-hidden="true">NE</div>
          <div>
            <p className="brand-name">NEW.ENGINE</p>
            <p className="brand-subtitle">Engine Audit Console</p>
          </div>
        </Link>
        <div className="topbar-status">
          <span className={`status-pill ${statusClass(run.status)}`}>
            <span className="status-dot" />{run.status.toUpperCase()}
          </span>
          <Link className={styles.navLink} href="/">Data</Link>
        </div>
      </header>

      <section className={styles.hero}>
        <div className={styles.heroCopy}>
          <p className="eyebrow">ENGINE CORE / EVIDENCE LAYER</p>
          <h1>Audit every candidate before release.</h1>
          <p>
            Run terbaru menampilkan kandidat terbaik hasil walk-forward untuk setiap posisi dan market.
            Seluruh output masih dikunci sebagai riset sampai release gate diterapkan.
          </p>
        </div>
        <div className={styles.heroMeta}>
          <span className="status-pill status-research">RESEARCH ONLY</span>
          <span className="version-tag mono">ENGINE {run.engineVersion}</span>
        </div>
      </section>

      <section className="metric-grid" aria-label="Engine run metrics">
        <article className="metric-card">
          <p>Audited markets</p>
          <strong>{audits.length}</strong>
          <span>dari {run.marketsLoaded} market valid</span>
        </article>
        <article className="metric-card">
          <p>All-position positive</p>
          <strong>{allPositiveMarkets}</strong>
          <span>lift positif pada 4 posisi</span>
        </article>
        <article className="metric-card">
          <p>Engine errors</p>
          <strong className={run.engineErrorCount ? "metric-warning" : ""}>{run.engineErrorCount}</strong>
          <span>validation: {run.validationErrorCount}</span>
        </article>
        <article className="metric-card accent-card">
          <p>Runtime</p>
          <strong className="timestamp-value">{formatDuration(run.startedAt, run.finishedAt)}</strong>
          <span>{run.source}</span>
        </article>
      </section>

      <section className={`panel ${styles.runPanel}`}>
        <div className={styles.runHeading}>
          <div>
            <p className="eyebrow">LATEST RUN</p>
            <h2>Execution record</h2>
          </div>
          <span className={`status-pill ${statusClass(run.status)}`}>{run.status.toUpperCase()}</span>
        </div>
        <div className={styles.runGrid}>
          <div className={styles.runItem}>
            <span>Run ID</span>
            <strong className="mono">{run.id}</strong>
          </div>
          <div className={styles.runItem}>
            <span>Started (WITA)</span>
            <strong className="mono">{formatTimestamp(run.startedAt)}</strong>
          </div>
          <div className={styles.runItem}>
            <span>Finished (WITA)</span>
            <strong className="mono">{formatTimestamp(run.finishedAt)}</strong>
          </div>
          <div className={styles.runItem}>
            <span>Evaluated</span>
            <strong className="mono">{run.marketsEvaluated}/{run.marketsLoaded}</strong>
          </div>
        </div>
        <div className={styles.configStrip} aria-label="Engine configuration">
          <span className={`${styles.configToken} mono`}>windows={configValue(configuration.windows)}</span>
          <span className={`${styles.configToken} mono`}>horizons={configValue(configuration.eval_horizons)}</span>
          <span className={`${styles.configToken} mono`}>top_k={configValue(configuration.top_k)}</span>
          <span className={`${styles.configToken} mono`}>min_train={configValue(configuration.min_train_size)}</span>
          <span className={`${styles.configToken} mono`}>half_life={configValue(configuration.recency_half_life)}</span>
        </div>
      </section>

      <EngineAuditList audits={audits} />

      <footer>
        <span>NEW.ENGINE Engine Audit Console</span>
        <span className="mono">RESEARCH ONLY · WALK-FORWARD · AUDITABLE</span>
      </footer>
    </main>
  );
}
