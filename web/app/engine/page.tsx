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

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
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

  const eligibleMarkets = audits.filter(
    (audit) => audit.marketReleaseGate.status === "eligible",
  ).length;
  const heldMarkets = audits.length - eligibleMarkets;
  const configuration = run.config;
  const gateConfiguration = asRecord(configuration.release_gate);

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
          <p className="eyebrow">ENGINE CORE / EVIDENCE GATE</p>
          <h1>Hold weak candidates before release.</h1>
          <p>
            Run terbaru menilai kandidat terbaik hasil walk-forward dengan release gate deterministik.
            Gate pass hanya berarti evidence minimum terpenuhi; seluruh output tetap research-only sampai
            prediction journal dan settlement tersedia.
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
          <p>Gate eligible</p>
          <strong>{eligibleMarkets}</strong>
          <span>4/4 posisi lulus</span>
        </article>
        <article className="metric-card">
          <p>Gate held</p>
          <strong className={heldMarkets ? "metric-warning" : ""}>{heldMarkets}</strong>
          <span>evidence belum lengkap</span>
        </article>
        <article className="metric-card accent-card">
          <p>Runtime</p>
          <strong className="timestamp-value">{formatDuration(run.startedAt, run.finishedAt)}</strong>
          <span>{run.source} · errors {run.engineErrorCount}</span>
        </article>
      </section>

      <section className={`panel ${styles.runPanel}`}>
        <div className={styles.runHeading}>
          <div>
            <p className="eyebrow">LATEST RUN</p>
            <h2>Execution and gate configuration</h2>
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
          <span className={`${styles.configToken} mono`}>gate_samples≥{configValue(gateConfiguration.min_sample_size)}</span>
          <span className={`${styles.configToken} mono`}>gate_lift≥{configValue(gateConfiguration.min_lift)}</span>
          <span className={`${styles.configToken} mono`}>miss≤{configValue(gateConfiguration.max_miss_streak)}</span>
          <span className={`${styles.configToken} mono`}>logloss≤{configValue(gateConfiguration.max_log_loss)}</span>
          <span className={`${styles.configToken} mono`}>brier≤{configValue(gateConfiguration.max_brier_score)}</span>
        </div>
      </section>

      <EngineAuditList audits={audits} />

      <footer>
        <span>NEW.ENGINE Evidence Gate Console</span>
        <span className="mono">RESEARCH ONLY · DETERMINISTIC CHECKS · AUDITABLE</span>
      </footer>
    </main>
  );
}
