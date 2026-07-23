"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import type { EngineMarketAudit } from "@/lib/engine-audit-types";

import styles from "./engine-audit-list.module.css";

type QualityFilter = "all" | "positive" | "attention";

const POSITION_LABELS = ["AS", "KOP", "KEPALA", "EKOR"];

function percent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function liftLabel(value: number): string {
  const points = value * 100;
  return `${points >= 0 ? "+" : ""}${points.toFixed(1)} pp`;
}

function hasPositiveLift(audit: EngineMarketAudit): boolean {
  return audit.positions.every((position) => position.selectedCandidate.lift > 0);
}

export function EngineAuditList({ audits }: { audits: EngineMarketAudit[] }) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<QualityFilter>("all");

  const filteredAudits = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return audits.filter((audit) => {
      const matchesQuery =
        !normalizedQuery ||
        audit.marketId.toLowerCase().includes(normalizedQuery) ||
        audit.marketName.toLowerCase().includes(normalizedQuery);
      const allPositive = hasPositiveLift(audit);
      const matchesFilter =
        filter === "all" ||
        (filter === "positive" && allPositive) ||
        (filter === "attention" && !allPositive);
      return matchesQuery && matchesFilter;
    });
  }, [audits, filter, query]);

  return (
    <section className={`panel ${styles.section}`}>
      <div className={styles.heading}>
        <div>
          <p className="eyebrow">LATEST ENGINE AUDITS</p>
          <h2>Market candidate registry</h2>
          <p className="muted">
            {filteredAudits.length} dari {audits.length} audit ditampilkan. Top digit adalah output riset,
            bukan rilis prediksi.
          </p>
        </div>
        <div className={styles.controls}>
          <label>
            <span className="sr-only">Cari audit market</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Cari market..."
              type="search"
              inputMode="search"
              autoComplete="off"
            />
          </label>
          <label>
            <span className="sr-only">Filter kualitas audit</span>
            <select
              value={filter}
              onChange={(event) => setFilter(event.target.value as QualityFilter)}
            >
              <option value="all">Semua audit</option>
              <option value="positive">Semua posisi lift positif</option>
              <option value="attention">Perlu perhatian</option>
            </select>
          </label>
        </div>
      </div>

      {filteredAudits.length ? (
        <div className={styles.list}>
          {filteredAudits.map((audit) => {
            const positivePositions = audit.positions.filter(
              (position) => position.selectedCandidate.lift > 0,
            ).length;

            return (
              <Link
                className={styles.cardLink}
                href={`/engine/markets/${encodeURIComponent(audit.marketId)}`}
                key={audit.marketId}
              >
                <article className={styles.card}>
                  <div className={styles.cardTop}>
                    <div className={styles.identity}>
                      <h3>{audit.marketName}</h3>
                      <p className="mono">{audit.marketId}</p>
                    </div>
                    <span className="status-pill status-research">RESEARCH</span>
                  </div>

                  <div className={styles.summary}>
                    <div>
                      <span>History</span>
                      <strong className="mono">{audit.historySize.toLocaleString("id-ID")}</strong>
                    </div>
                    <div>
                      <span>Candidates</span>
                      <strong className="mono">{audit.candidateCount.toLocaleString("id-ID")}</strong>
                    </div>
                    <div>
                      <span>Positive lift</span>
                      <strong className="mono">{positivePositions}/4 posisi</strong>
                    </div>
                  </div>

                  <div className={styles.positionGrid}>
                    {audit.positions.map((position) => {
                      const candidate = position.selectedCandidate;
                      const liftClass =
                        candidate.lift > 0 ? styles.liftPositive : styles.liftNegative;

                      return (
                        <div className={styles.position} key={position.position}>
                          <div className={styles.positionHeader}>
                            <strong>{POSITION_LABELS[position.position] ?? `P${position.position}`}</strong>
                            <span className={liftClass}>{liftLabel(candidate.lift)}</span>
                          </div>
                          <div className={styles.digits}>
                            {position.topDigits.map((digit) => (
                              <span className={`${styles.digit} mono`} key={digit}>{digit}</span>
                            ))}
                          </div>
                          <div className={styles.positionMeta}>
                            <span className="mono">{candidate.modelName}</span>
                            <span className="mono">W{candidate.window} · H{candidate.horizon}</span>
                            <span className="mono">Recent {percent(candidate.recentHitRate)}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <span className={styles.action}>
                    Buka audit lengkap <span aria-hidden="true">→</span>
                  </span>
                </article>
              </Link>
            );
          })}
        </div>
      ) : (
        <div className={styles.empty}>Tidak ada audit yang cocok dengan pencarian atau filter.</div>
      )}
    </section>
  );
}
