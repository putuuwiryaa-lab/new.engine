import Link from "next/link";

import { getLatestMarketAudit } from "@/lib/engine-audits";

import styles from "../../engine.module.css";
import gateStyles from "./gate.module.css";

export const dynamic = "force-dynamic";

const POSITION_LABELS = ["AS", "KOP", "KEPALA", "EKOR"];

function formatTimestamp(value: string | null): string {
  if (!value) return "Belum ada";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Timestamp invalid";
  return new Intl.DateTimeFormat("id-ID", {
    timeZone: "Asia/Makassar",
    dateStyle: "medium",
    timeStyle: "medium",
    hour12: false,
  }).format(date);
}

function percent(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

function lift(value: number): string {
  const points = value * 100;
  return `${points >= 0 ? "+" : ""}${points.toFixed(2)} pp`;
}

function reasonLabel(value: string): string {
  return value.replaceAll("_", " ").toUpperCase();
}

function checkLabel(value: string): string {
  return value.replaceAll("_", " ");
}

function checkNumber(value: number): string {
  if (Number.isInteger(value)) return String(value);
  return value.toFixed(4);
}

export default async function EngineMarketAuditPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const marketId = decodeURIComponent(id);
  const audit = await getLatestMarketAudit(marketId);

  if (!audit) {
    return (
      <main className={`shell ${styles.shell}`}>
        <header className="topbar">
          <Link className="brand-block brand-link" href="/engine">
            <div className="brand-mark" aria-hidden="true">NE</div>
            <div>
              <p className="brand-name">NEW.ENGINE</p>
              <p className="brand-subtitle">Engine Audit Console</p>
            </div>
          </Link>
          <Link className={styles.navLink} href="/engine">← Audit registry</Link>
        </header>
        <section className={`panel ${styles.emptyPanel}`}>
          <p className="eyebrow">AUDIT NOT FOUND</p>
          <h2>Belum ada audit untuk {marketId}.</h2>
          <p className="muted">Market ini akan muncul setelah full pipeline berhasil mengevaluasinya.</p>
        </section>
      </main>
    );
  }

  const marketEligible = audit.marketReleaseGate.status === "eligible";
  const heldPositions = audit.positions
    .filter((position) => position.releaseGate.status === "hold")
    .map((position) => POSITION_LABELS[position.position] ?? `P${position.position}`);

  return (
    <main className={`shell ${styles.shell}`}>
      <header className="topbar">
        <Link className="brand-block brand-link" href="/engine">
          <div className="brand-mark" aria-hidden="true">NE</div>
          <div>
            <p className="brand-name">NEW.ENGINE</p>
            <p className="brand-subtitle">Evidence Gate Console</p>
          </div>
        </Link>
        <div className="topbar-status">
          <Link className={styles.navLink} href={`/markets/${encodeURIComponent(audit.marketId)}`}>Data</Link>
          <Link className={styles.navLink} href="/engine">Audits</Link>
        </div>
      </header>

      <section className={`panel ${styles.detailHero}`}>
        <div>
          <p className="eyebrow">LATEST MARKET AUDIT</p>
          <h1>{audit.marketName}</h1>
          <p className="mono dim">{audit.marketId}</p>
        </div>
        <div className={styles.heroMeta}>
          <span className={`status-pill ${marketEligible ? "status-ok" : "status-warn"}`}>
            {marketEligible ? "GATE PASS" : "GATE HOLD"}
          </span>
          <span className="status-pill status-research">{audit.releaseStatus.toUpperCase()}</span>
          <span className="version-tag mono">RUN {audit.runId.slice(0, 8)}</span>
        </div>
      </section>

      <section className="metric-grid detail-metrics">
        <article className="metric-card">
          <p>History depth</p>
          <strong>{audit.historySize.toLocaleString("id-ID")}</strong>
          <span>result yang dianalisis</span>
        </article>
        <article className="metric-card">
          <p>Position gate</p>
          <strong>{audit.marketReleaseGate.passedPositions}/{audit.marketReleaseGate.requiredPositions}</strong>
          <span>posisi memenuhi seluruh check</span>
        </article>
        <article className="metric-card wide-metric">
          <p>Generated (WITA)</p>
          <strong className="timestamp-value">{formatTimestamp(audit.generatedAt)}</strong>
          <span>history update: {formatTimestamp(audit.historyUpdatedAt)}</span>
        </article>
      </section>

      <section className={`panel ${gateStyles.marketGate}`}>
        <div className={gateStyles.marketGateTop}>
          <div>
            <p className="eyebrow">MARKET RELEASE GATE</p>
            <h2>{marketEligible ? "Minimum evidence satisfied" : "Candidate release is held"}</h2>
            <p>
              Gate pass tetap research-only. Prediction journal dan settlement wajib tersedia sebelum
              output dapat dipertimbangkan untuk rilis produksi.
            </p>
          </div>
          <span className={`status-pill ${marketEligible ? "status-ok" : "status-warn"}`}>
            {marketEligible ? "ELIGIBLE 4/4" : `HELD ${audit.marketReleaseGate.passedPositions}/4`}
          </span>
        </div>
        <div className={gateStyles.reasonList}>
          {marketEligible ? (
            <span className={`${gateStyles.noReason} mono`}>ALL_POSITION_GATES_PASS</span>
          ) : (
            heldPositions.map((position) => (
              <span className={`${gateStyles.reason} mono`} key={position}>{position}_HELD</span>
            ))
          )}
        </div>
      </section>

      <section className={styles.positionDetailGrid}>
        {audit.positions.map((position) => {
          const candidate = position.selectedCandidate;
          const gatePass = position.releaseGate.status === "pass";
          const maximumProbability = Math.max(
            ...Object.values(position.probabilities),
            0.000001,
          );

          return (
            <article className={`panel ${styles.positionDetail}`} key={position.position}>
              <div className={styles.positionHeading}>
                <div>
                  <p className="eyebrow">POSITION {position.position}</p>
                  <h2>{POSITION_LABELS[position.position] ?? `P${position.position}`}</h2>
                  <p className="mono">{candidate.modelName} · W{candidate.window} · H{candidate.horizon}</p>
                </div>
                <span className={`status-pill ${gatePass ? "status-ok" : "status-warn"}`}>
                  {gatePass ? "GATE PASS" : "GATE HOLD"}
                </span>
              </div>

              <div className={gateStyles.positionGate}>
                <div className={gateStyles.positionGateHeader}>
                  <strong>Evidence checks</strong>
                  <span className={`mono ${gatePass ? gateStyles.pass : gateStyles.hold}`}>
                    LIFT {lift(candidate.lift)}
                  </span>
                </div>
                <div className={gateStyles.reasonList}>
                  {position.releaseGate.reasons.length ? (
                    position.releaseGate.reasons.map((reason) => (
                      <span className={`${gateStyles.reason} mono`} key={reason}>{reasonLabel(reason)}</span>
                    ))
                  ) : (
                    <span className={`${gateStyles.noReason} mono`}>ALL_CHECKS_PASS</span>
                  )}
                </div>
                <div className={gateStyles.checkGrid}>
                  {Object.entries(position.releaseGate.checks).map(([name, check]) => (
                    <div className={gateStyles.check} key={name}>
                      <span className={gateStyles.checkName}>{checkLabel(name)}</span>
                      <span className={`${gateStyles.checkValue} mono ${check.passed ? gateStyles.pass : gateStyles.hold}`}>
                        {checkNumber(check.actual)} {check.operator} {checkNumber(check.threshold)} · {check.passed ? "PASS" : "HOLD"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className={styles.topDigits} aria-label="Top digits">
                {position.topDigits.map((digit) => (
                  <span className={`${styles.topDigit} mono`} key={digit}>{digit}</span>
                ))}
              </div>

              <div className={styles.candidateMetrics}>
                <div className={styles.metric}>
                  <span>Hit rate</span>
                  <strong className="mono">{percent(candidate.hitRate)}</strong>
                </div>
                <div className={styles.metric}>
                  <span>Baseline</span>
                  <strong className="mono">{percent(candidate.baselineHitRate)}</strong>
                </div>
                <div className={styles.metric}>
                  <span>Recent hit rate</span>
                  <strong className="mono">{percent(candidate.recentHitRate)}</strong>
                </div>
                <div className={styles.metric}>
                  <span>Samples</span>
                  <strong className="mono">{candidate.sampleSize}</strong>
                </div>
                <div className={styles.metric}>
                  <span>Longest miss</span>
                  <strong className="mono">{candidate.longestMissStreak}</strong>
                </div>
                <div className={styles.metric}>
                  <span>Mean actual probability</span>
                  <strong className="mono">{percent(candidate.meanActualProbability)}</strong>
                </div>
                <div className={styles.metric}>
                  <span>Log loss</span>
                  <strong className="mono">{candidate.logLoss.toFixed(4)}</strong>
                </div>
                <div className={styles.metric}>
                  <span>Brier score</span>
                  <strong className="mono">{candidate.brierScore.toFixed(4)}</strong>
                </div>
                <div className={styles.metric}>
                  <span>Hits</span>
                  <strong className="mono">{candidate.hits}/{candidate.sampleSize}</strong>
                </div>
              </div>

              <div className={styles.probabilityList} aria-label="Digit probability distribution">
                {position.rankedDigits.map((digit) => {
                  const probability = position.probabilities[String(digit)] ?? 0;
                  const relativeWidth = Math.max(2, (probability / maximumProbability) * 100);
                  return (
                    <div className={styles.probabilityRow} key={digit}>
                      <span className={`${styles.probabilityDigit} mono`}>{digit}</span>
                      <div className={styles.probabilityTrack}>
                        <i className={styles.probabilityBar} style={{ width: `${relativeWidth}%` }} />
                      </div>
                      <span className={`${styles.probabilityValue} mono`}>{percent(probability)}</span>
                    </div>
                  );
                })}
              </div>
            </article>
          );
        })}
      </section>

      <footer>
        <span>{audit.marketName}</span>
        <span className="mono">EVIDENCE GATE · RESEARCH ONLY · NOT A PRODUCTION RELEASE</span>
      </footer>
    </main>
  );
}
