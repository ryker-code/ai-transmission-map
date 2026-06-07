"use client";
import useSWR from "swr";
import Link from "next/link";
import type { WatchlistResponse } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const fetcher = (url: string) => fetch(url).then((r) => r.json());

const MOMENTUM_COLORS: Record<string, string> = {
  strong_bull: "text-emerald-400 bg-emerald-900/30",
  bull: "text-green-400 bg-green-900/30",
  neutral: "text-slate-400 bg-slate-800",
  bear: "text-orange-400 bg-orange-900/30",
  strong_bear: "text-red-400 bg-red-900/30",
};

export default function WatchlistPage() {
  const { data, error, isLoading, mutate } = useSWR<WatchlistResponse>(
    `${API_URL}/watchlist/`,
    fetcher,
    { refreshInterval: 30_000, revalidateOnFocus: false }
  );

  async function handleRemove(entityId: string) {
    await fetch(`${API_URL}/watchlist/${entityId}`, { method: "DELETE" });
    mutate();
  }

  const entries = data?.entries ?? [];

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold text-white mb-1">Watchlist</h1>
      <p className="text-slate-400 text-sm mb-6">
        Starred entities — live bottleneck score monitoring
      </p>

      {isLoading && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-400 text-sm animate-pulse">
          Loading watchlist…
        </div>
      )}
      {error && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-red-400 text-sm">
          Failed to load watchlist — API may be unavailable
        </div>
      )}
      {!isLoading && !error && entries.length === 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-10 text-center space-y-3">
          <p className="text-3xl">★</p>
          <p className="text-slate-300 font-medium">Your watchlist is empty</p>
          <p className="text-slate-500 text-sm">Open any entity page and click ☆ to add it here</p>
          <Link
            href="/graph"
            className="inline-block mt-2 px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm hover:bg-indigo-500 transition-colors"
          >
            Browse Graph →
          </Link>
        </div>
      )}
      {entries.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-xs">
                <th className="text-left px-5 py-3 font-medium">Entity</th>
                <th className="text-left px-4 py-3 font-medium">Ticker</th>
                <th className="text-right px-4 py-3 font-medium">Score</th>
                <th className="text-right px-4 py-3 font-medium">24h Δ</th>
                <th className="text-left px-4 py-3 font-medium">Momentum</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.entity_id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                  <td className="px-5 py-3">
                    <Link href={`/entities/${e.entity_id}`} className="text-white font-medium hover:text-indigo-300 transition-colors">
                      {e.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    {e.ticker ? (
                      <span className="text-xs font-mono text-slate-400">{e.ticker}</span>
                    ) : (
                      <span className="text-slate-600">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {e.bottleneck_score != null ? (
                      <span className="text-indigo-300 font-mono font-medium">
                        {e.bottleneck_score.toFixed(1)}
                      </span>
                    ) : (
                      <span className="text-slate-600">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {e.score_delta_24h === 0 ? (
                      <span className="text-slate-500">—</span>
                    ) : (
                      <span className={e.score_delta_24h > 0 ? "text-emerald-400" : "text-red-400"}>
                        {e.score_delta_24h > 0 ? "+" : ""}{e.score_delta_24h.toFixed(1)}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${MOMENTUM_COLORS[e.momentum] ?? MOMENTUM_COLORS.neutral}`}>
                      {e.momentum.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleRemove(e.entity_id)}
                      className="text-amber-400 hover:text-slate-400 transition-colors text-base"
                      title="Remove from watchlist"
                    >
                      ★
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
