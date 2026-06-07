"use client";
import { use, useState, useEffect } from "react";
import useSWR from "swr";
import Link from "next/link";
import type { EntityDetailResponse, ClaimSummary, MarketSignalEntry } from "@/lib/types";

const API_URL_GLOBAL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const fetcher = (url: string) => fetch(url).then((r) => r.json());

const TYPE_COLORS: Record<string, string> = {
  public_co: "bg-indigo-900/60 text-indigo-300",
  private_co: "bg-violet-900/60 text-violet-300",
  utility: "bg-amber-900/60 text-amber-300",
  asset: "bg-emerald-900/60 text-emerald-300",
  technology: "bg-cyan-900/60 text-cyan-300",
  geo: "bg-rose-900/60 text-rose-300",
  market: "bg-slate-700 text-slate-300",
};

const DIRECTION_COLOR: Record<string, string> = {
  positive: "text-emerald-400",
  negative: "text-rose-400",
};

function ScoreBar({ value, max = 100 }: { value: number; max?: number }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="w-full bg-slate-800 rounded-full h-1.5">
      <div className="bg-indigo-500 h-1.5 rounded-full" style={{ width: `${pct}%` }} />
    </div>
  );
}

function ClaimTable({ claims, label }: { claims: ClaimSummary[]; label: string }) {
  if (!claims.length) return (
    <p className="text-xs text-slate-500 italic">No {label.toLowerCase()} claims in graph.</p>
  );
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs text-left">
        <thead>
          <tr className="text-slate-400 border-b border-slate-800">
            <th className="pb-2 pr-3">Subject</th>
            <th className="pb-2 pr-3">Predicate</th>
            <th className="pb-2 pr-3">Object</th>
            <th className="pb-2 pr-3">Dir</th>
            <th className="pb-2 pr-3">Conf</th>
            <th className="pb-2">Horizon</th>
          </tr>
        </thead>
        <tbody>
          {claims.map((c, i) => (
            <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30">
              <td className="py-1.5 pr-3 text-slate-300 max-w-[120px] truncate">{c.subject}</td>
              <td className="py-1.5 pr-3 text-indigo-400 font-mono">{c.predicate}</td>
              <td className="py-1.5 pr-3 text-slate-300 max-w-[120px] truncate">{c.object}</td>
              <td className={`py-1.5 pr-3 font-medium ${DIRECTION_COLOR[c.direction] ?? "text-slate-400"}`}>
                {c.direction === "positive" ? "+" : "−"}
              </td>
              <td className="py-1.5 pr-3 text-slate-300">{(c.confidence * 100).toFixed(0)}%</td>
              <td className="py-1.5 text-slate-400">{c.horizon}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function EntityDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, error, isLoading } = useSWR<EntityDetailResponse>(
    `${API_BASE}/entities/${id}`,
    fetcher
  );
  const { data: marketData } = useSWR<{ signals: MarketSignalEntry[] }>(
    `${API_BASE}/market/signals`,
    fetcher,
    { revalidateOnFocus: false }
  );
  const [isWatched, setIsWatched] = useState(false);

  useEffect(() => {
    if (!id) return;
    fetch(`${API_URL_GLOBAL}/watchlist/`)
      .then((r) => r.json())
      .then((d) => {
        const watched = (d.entries ?? []).some((e: { entity_id: string }) => e.entity_id === id);
        setIsWatched(watched);
      })
      .catch(() => {});
  }, [id]);

  async function toggleWatch() {
    const method = isWatched ? "DELETE" : "POST";
    const resp = await fetch(`${API_URL_GLOBAL}/watchlist/${id}`, { method });
    if (resp.ok) setIsWatched(!isWatched);
  }

  const marketSignal = data?.ticker
    ? marketData?.signals.find((s) => s.ticker === data.ticker?.toUpperCase())
    : null;

  if (isLoading) return (
    <div className="text-slate-400 text-sm animate-pulse">Loading entity...</div>
  );
  if (error || !data) return (
    <div className="text-red-400 text-sm">Entity not found or API unavailable.</div>
  );

  const typeColor = TYPE_COLORS[data.entity_type] ?? "bg-slate-700 text-slate-300";
  const score = data.bottleneck_score ?? 0;

  return (
    <div className="max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-white">{data.canonical_name}</h1>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${typeColor}`}>
              {data.entity_type}
            </span>
            {data.ticker && (
              <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                {data.ticker}
              </span>
            )}
          </div>
          {data.sector && <p className="text-sm text-slate-400">{data.sector}{data.sub_sector ? ` · ${data.sub_sector}` : ""}</p>}
          {data.aliases.length > 0 && (
            <p className="text-xs text-slate-500 mt-1">Also known as: {data.aliases.join(", ")}</p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={toggleWatch}
            className={`text-xl transition-colors ${isWatched ? "text-amber-400 hover:text-slate-400" : "text-slate-600 hover:text-amber-400"}`}
            title={isWatched ? "Remove from watchlist" : "Add to watchlist"}
          >
            {isWatched ? "★" : "☆"}
          </button>
          <Link href="/graph" className="text-xs text-indigo-400 hover:text-indigo-300">← Graph</Link>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Bottleneck Score card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <p className="text-xs text-slate-400 mb-2">Bottleneck Score</p>
          <p className="text-4xl font-bold text-white mb-3">{score.toFixed(1)}<span className="text-lg text-slate-400">/100</span></p>
          {data.bottleneck_components && (
            <div className="space-y-2">
              {Object.entries(data.bottleneck_components)
                .filter(([k]) => k !== "raw_score")
                .map(([k, v]) => (
                  <div key={k}>
                    <div className="flex justify-between text-xs text-slate-400 mb-0.5">
                      <span>{k.replace(/_/g, " ")}</span>
                      <span>{typeof v === "number" ? v.toFixed(3) : v}</span>
                    </div>
                    {typeof v === "number" && <ScoreBar value={v} max={k === "house_view_weight" ? 3 : 1} />}
                  </div>
                ))}
            </div>
          )}
        </div>

        {/* Market Signals card */}
        {data.ticker && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <p className="text-xs text-slate-400 mb-3">Market Signals</p>
            {marketSignal ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono text-white">{data.ticker}</span>
                  <span className={`text-sm font-mono font-bold ${marketSignal.rel_perf_30d >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {marketSignal.rel_perf_30d >= 0 ? "+" : ""}{(marketSignal.rel_perf_30d * 100).toFixed(1)}%
                  </span>
                  <span className="text-xs text-slate-500">vs SPY 30d</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${
                    marketSignal.momentum === "strong_bull" ? "bg-emerald-900/40 text-emerald-300 border-emerald-700/40" :
                    marketSignal.momentum === "bull" ? "bg-emerald-900/20 text-emerald-400 border-emerald-800/40" :
                    marketSignal.momentum === "bear" ? "bg-red-900/40 text-red-300 border-red-700/40" :
                    marketSignal.momentum === "strong_bear" ? "bg-red-900/60 text-red-200 border-red-700/60" :
                    "bg-slate-700/40 text-slate-300 border-slate-600/40"
                  }`}>
                    {marketSignal.momentum.replace("_", " ")}
                  </span>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Vol percentile</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full bg-amber-500 rounded-full" style={{ width: `${marketSignal.vol_percentile}%` }} />
                    </div>
                    <span className="text-xs text-slate-400 font-mono">{marketSignal.vol_percentile}p</span>
                  </div>
                </div>
                <p className="text-xs text-slate-600">Mock data — not live</p>
              </div>
            ) : (
              <p className="text-xs text-slate-500">No market data for {data.ticker}</p>
            )}
          </div>
        )}

        {/* House View card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <p className="text-xs text-slate-400 mb-2">House View</p>
          {data.house_view ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  data.house_view.conviction === "high" ? "bg-emerald-900/60 text-emerald-300" :
                  data.house_view.conviction === "low" ? "bg-rose-900/60 text-rose-300" :
                  "bg-slate-700 text-slate-300"
                }`}>{data.house_view.conviction.toUpperCase()}</span>
                <span className="text-sm text-white">{data.house_view.weight_override}× weight</span>
              </div>
              {data.house_view.analyst_note && (
                <p className="text-xs text-slate-400 italic">&ldquo;{data.house_view.analyst_note}&rdquo;</p>
              )}
              <Link href="/house-view" className="text-xs text-indigo-400 hover:text-indigo-300">Edit →</Link>
            </div>
          ) : (
            <div className="text-slate-500 text-sm space-y-2">
              <p>No house view set</p>
              <Link href="/house-view" className="text-xs text-indigo-400 hover:text-indigo-300">Set conviction →</Link>
            </div>
          )}
        </div>
      </div>

      {/* Claims */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-white mb-3">
          Outbound Claims <span className="text-slate-400 font-normal">({data.outbound_claims.length})</span>
        </h2>
        <ClaimTable claims={data.outbound_claims} label="Outbound" />
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-white mb-3">
          Inbound Claims <span className="text-slate-400 font-normal">({data.inbound_claims.length})</span>
        </h2>
        <ClaimTable claims={data.inbound_claims} label="Inbound" />
      </div>

      {/* Related entities */}
      {data.related_entities.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-3">Related Entities</h2>
          <div className="flex gap-3">
            {data.related_entities.map((e) => (
              <Link key={e.id} href={`/entities/${e.id}`}
                className="flex-1 bg-slate-800 border border-slate-700 rounded-lg p-3 hover:border-indigo-500 transition-colors">
                <p className="text-sm font-medium text-white truncate">{e.canonical_name}</p>
                <p className="text-xs text-slate-400 mt-0.5">{e.entity_type} · {e.claim_count} claims</p>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
