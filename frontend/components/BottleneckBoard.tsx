"use client";
import useSWR from "swr";
import type { BottlenecksResponse, BottleneckEntry } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const fetcher = (url: string) => fetch(url).then((r) => r.json());

const REGIME_COLORS: Record<string, string> = {
  AI_CAPEX_EXPANSION: "text-indigo-400 bg-indigo-900/30 border-indigo-700/40",
  SUPPLY_CHAIN_STRESS: "text-amber-400 bg-amber-900/30 border-amber-700/40",
  GRID_BOTTLENECK: "text-red-400 bg-red-900/30 border-red-700/40",
  POWER_PRICE_SPREAD: "text-emerald-400 bg-emerald-900/30 border-emerald-700/40",
  REGULATORY: "text-purple-400 bg-purple-900/30 border-purple-700/40",
  NUCLEAR_RENAISSANCE: "text-cyan-400 bg-cyan-900/30 border-cyan-700/40",
};

function ScoreBar({ score }: { score: number }) {
  return (
    <div className="w-24 h-1.5 bg-slate-700 rounded-full overflow-hidden">
      <div
        className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-indigo-300"
        style={{ width: `${Math.round(score * 100)}%` }}
      />
    </div>
  );
}

function BottleneckRow({ entry }: { entry: BottleneckEntry }) {
  const regimeClass = REGIME_COLORS[entry.regime_tag] ?? "text-slate-400 bg-slate-800 border-slate-700";
  return (
    <div className="flex items-center gap-4 px-4 py-3 border-b border-slate-800/50 last:border-0 hover:bg-slate-800/30 transition-colors">
      <span className="w-7 text-xs text-slate-500 font-mono text-right flex-shrink-0">
        {entry.rank}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white font-medium truncate">{entry.entity_name}</p>
        <p className="text-xs text-slate-500 mt-0.5">
          {entry.components.claim_count} claims · score {entry.score.toFixed(3)}
        </p>
      </div>
      <ScoreBar score={entry.score} />
      <span className={`hidden sm:inline-flex text-xs px-2 py-0.5 rounded-full border flex-shrink-0 ${regimeClass}`}>
        {entry.regime_tag.replace(/_/g, " ")}
      </span>
    </div>
  );
}

export default function BottleneckBoard({ limit = 20 }: { limit?: number }) {
  const { data, error, isLoading } = useSWR<BottlenecksResponse>(
    `${API_BASE}/bottlenecks/?limit=${limit}`,
    fetcher,
    { refreshInterval: 60000, revalidateOnFocus: false, keepPreviousData: true }
  );

  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-800">
          <span className="text-sm font-medium text-slate-300">Top Bottlenecks</span>
        </div>
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex items-center gap-4 px-4 py-3 border-b border-slate-800/50 last:border-0">
            <div className="w-7 h-3 bg-slate-800 rounded animate-pulse" />
            <div className="flex-1 space-y-1.5">
              <div className="h-3 bg-slate-800 rounded animate-pulse w-48" />
              <div className="h-2 bg-slate-800/60 rounded animate-pulse w-32" />
            </div>
            <div className="h-1.5 w-24 bg-slate-800 rounded-full animate-pulse" />
          </div>
        ))}
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center text-slate-500 text-sm">
        Could not load bottlenecks — ensure backend is running on port 8000.
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <span className="text-sm font-medium text-slate-300">Top Bottlenecks</span>
        <span className="text-xs text-slate-500">{data.total} entities scored</span>
      </div>
      {data.bottlenecks.length === 0 ? (
        <div className="px-4 py-12 text-center">
          <div className="text-slate-600 text-3xl mb-3">◎</div>
          <p className="text-slate-400 text-sm font-medium">No bottlenecks scored yet.</p>
          <p className="text-slate-500 text-xs mt-1">Ingest evidence to begin transmission chain analysis.</p>
          <a href="/evidence" className="mt-3 inline-block text-xs text-indigo-400 hover:text-indigo-300">Add evidence →</a>
        </div>
      ) : (
        data.bottlenecks.map((entry) => (
          <BottleneckRow key={entry.entity_id} entry={entry} />
        ))
      )}
    </div>
  );
}
