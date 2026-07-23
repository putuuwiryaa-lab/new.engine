"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import type { MarketSummary } from "@/lib/markets";

type Filter = "all" | "primary" | "rajapaito" | "stale";

function formatUpdatedAt(value: string | null): string {
  if (!value) return "Belum ada";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Invalid";
  return new Intl.DateTimeFormat("id-ID", {
    timeZone: "Asia/Makassar",
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function MarketStatus({ isStale }: { isStale: boolean }) {
  return (
    <span className={`status-pill ${isStale ? "status-warn" : "status-ok"}`}>
      <span className="status-dot" />
      {isStale ? "STALE" : "FRESH"}
    </span>
  );
}

export function MarketTable({ markets }: { markets: MarketSummary[] }) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");

  const filteredMarkets = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return markets.filter((market) => {
      const matchesQuery =
        !normalizedQuery ||
        market.id.toLowerCase().includes(normalizedQuery) ||
        market.name.toLowerCase().includes(normalizedQuery);
      const matchesFilter =
        filter === "all" ||
        (filter === "primary" && market.source === "Primary") ||
        (filter === "rajapaito" && market.source === "Rajapaito") ||
        (filter === "stale" && market.isStale);
      return matchesQuery && matchesFilter;
    });
  }, [filter, markets, query]);

  return (
    <section className="panel market-panel" id="registry">
      <div className="panel-heading market-toolbar">
        <div>
          <p className="eyebrow">DATA REGISTRY</p>
          <h2>Market snapshots</h2>
          <p className="muted">{filteredMarkets.length} dari {markets.length} market ditampilkan.</p>
        </div>
        <div className="toolbar-controls">
          <label className="search-field">
            <span className="sr-only">Cari market</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Cari market..."
              type="search"
              inputMode="search"
              autoComplete="off"
            />
          </label>
          <label className="filter-field">
            <span className="sr-only">Filter market</span>
            <select value={filter} onChange={(event) => setFilter(event.target.value as Filter)}>
              <option value="all">Semua sumber</option>
              <option value="primary">Primary</option>
              <option value="rajapaito">Rajapaito</option>
              <option value="stale">Data stale</option>
            </select>
          </label>
        </div>
      </div>

      <div className="market-card-list" aria-label="Daftar market">
        {filteredMarkets.map((market) => (
          <Link
            className="market-card-link"
            href={`/markets/${encodeURIComponent(market.id)}`}
            key={market.id}
          >
            <article className="market-card">
              <div className="market-card-top">
                <div className="market-card-identity">
                  <span className="market-order mono">#{market.order}</span>
                  <div>
                    <h3>{market.name}</h3>
                    <p className="mono">{market.id}</p>
                  </div>
                </div>
                <MarketStatus isStale={market.isStale} />
              </div>

              <div className="market-card-result">
                <span>Latest result</span>
                <strong className="mono">{market.latestResult ?? "—"}</strong>
              </div>

              <div className="market-card-meta">
                <div>
                  <span>Sumber</span>
                  <strong>{market.source}</strong>
                </div>
                <div>
                  <span>History</span>
                  <strong className="mono">{market.historyCount.toLocaleString("id-ID")}</strong>
                </div>
                <div className="market-card-updated">
                  <span>Updated (WITA)</span>
                  <strong className="mono">{formatUpdatedAt(market.updatedAt)}</strong>
                </div>
              </div>

              <span className="market-card-action">Buka detail <span aria-hidden="true">→</span></span>
            </article>
          </Link>
        ))}
      </div>

      <div className="table-wrap desktop-market-table">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Market</th>
              <th>Sumber</th>
              <th>Latest</th>
              <th>History</th>
              <th>Updated (WITA)</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredMarkets.map((market) => (
              <tr key={market.id}>
                <td className="mono dim">{market.order}</td>
                <td>
                  <Link className="market-link" href={`/markets/${encodeURIComponent(market.id)}`}>
                    <strong>{market.name}</strong>
                    <span className="mono">{market.id}</span>
                  </Link>
                </td>
                <td><span className="source-tag">{market.source}</span></td>
                <td className="mono result-cell">{market.latestResult ?? "—"}</td>
                <td className="mono">{market.historyCount.toLocaleString("id-ID")}</td>
                <td className="mono small">{formatUpdatedAt(market.updatedAt)}</td>
                <td><MarketStatus isStale={market.isStale} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredMarkets.length === 0 ? (
        <div className="empty-state">Tidak ada market yang cocok dengan filter.</div>
      ) : null}
    </section>
  );
}
