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
    <section className="panel market-panel">
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
            />
          </label>
          <select value={filter} onChange={(event) => setFilter(event.target.value as Filter)}>
            <option value="all">Semua sumber</option>
            <option value="primary">Primary</option>
            <option value="rajapaito">Rajapaito</option>
            <option value="stale">Data stale</option>
          </select>
        </div>
      </div>

      <div className="table-wrap">
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
                <td>
                  <span className={`status-pill ${market.isStale ? "status-warn" : "status-ok"}`}>
                    <span className="status-dot" />
                    {market.isStale ? "STALE" : "FRESH"}
                  </span>
                </td>
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
