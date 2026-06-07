"use client";
import useSWR from "swr";
import Link from "next/link";
import type { WatchlistResponse, WatchlistEntry } from "@/lib/types";

const API_URL = '/api/proxy';
const fetcher = (url: string) => fetch(url).then((r) => r.json());

function MomentumBadge({ momentum }: { momentum: string }) {
  const colors: Record<string, string> = {
    strong_bull: "text-emerald-400 bg-emerald-900/30 border-emerald-700/40",
    bull: "text-green-400 bg-green-900/30 border-green-700/40",
    neutral: "text-slate-400 bg-slate-800 border-slate-700",
    bear: "text-orange-400 bg-orange-900/30 border-orange-700/40",
    strong_bear: "text-red-400 bg-red-900/30 border-red-700/40",
  };
  const arrows: Record<string, string> = {
    strong_bull: "↑↑", bull: "↑", neutral: "→", bear: "↓", strong_bear: "↓↓",
  };
  const cls = colors[momentum] ?? colors.neutral;
  const arrow = arrows[momentum] ?? "→";
  return (
    <span className={`px-1.5 py-0.5 rounded text-xs border ${cls}`}>
      {arrow} {momentum.replace("_", " ")}
    </span>
  );
}

function DeltaBadge({ delta }: { delta: number }) {
  if (delta === 0) return <span className="text-slate-500 text-xs">—</span>;
  const sign = delta > 0 ? "+" : "";
  const cls = delta > 0 ? "text-emerald-400" : "text-red-400";
  return <span className={`text-xs font-medium ${cls}`}>{sign}{delta.toFixed(1)} pts</span>;
}

async function toggleWatch(entityId: string, isWatched: boolean) {
  const method = isWatched ? "DELETE" : "POST";
  await fetch(`${API_URL}/watchlist/${entityId}`, { method });
}

export function WatchlistPanel() {
  const { data, error, isLoading, mutate } = useSWR<WatchlistResponse>(
    `${API_URL}/watchlist/`,
    fetcher,
    { refreshInterval: 30_000, revalidateOnFocus: false }
  );

  const entries = data?.entries ?? [];

  async function handleRemove(entityId: string) {
    await toggleWatch(entityId, true);
    mutate();
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-white">Watchlist</p>
          <p className="text-xs text-slate-400 mt-0.5">Starred entities — live score monitoring</p>
        </div>
        <Link href="/watchlist" className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
          Manage →
        </Link>
      </div>

      {isLoading && (
        <div className="px-5 py-8 text-center text-slate-500 text-sm">Loading watchlist…</div>
      )}
      {error && (
        <div className="px-5 py-8 text-center text-red-400 text-sm">Failed to load watchlist</div>
      )}
      {!isLoading && !error && entries.length === 0 && (
        <div className="px-5 py-8 text-center space-y-2">
          <p className="text-slate-400 text-sm">No entities starred yet</p>
          <p className="text-slate-500 text-xs">Open any entity and click ★ to add it here</p>
          <Link
            href="/entities"
            className="inline-block mt-2 px-3 py-1.5 rounded-lg bg-slate-800 text-xs text-slate-300 hover:bg-slate-700 transition-colors"
          >
            Browse Entities →
          </Link>
        </div>
      )}
      {entries.length > 0 && (
        <div className="divide-y divide-slate-800">
          {entries.map((e) => (
            <div key={e.entity_id} className="px-5 py-3 flex items-center gap-3 hover:bg-slate-800/40 transition-colors">
              <Link href={`/entities/${e.entity_id}`} className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm text-white font-medium truncate">{e.name}</p>
                  {e.ticker && (
                    <span className="text-xs text-slate-500 font-mono shrink-0">{e.ticker}</span>
                  )}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  {e.bottleneck_score != null && (
                    <span className="text-xs text-indigo-300">Score: {e.bottleneck_score.toFixed(1)}</span>
                  )}
                  <DeltaBadge delta={e.score_delta_24h} />
                  <MomentumBadge momentum={e.momentum} />
                </div>
              </Link>
              <button
                onClick={() => handleRemove(e.entity_id)}
                className="text-amber-400 hover:text-slate-400 transition-colors text-sm shrink-0"
                title="Remove from watchlist"
              >
                ★
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export async function watchEntity(entityId: string) {
  await fetch(`${API_URL}/watchlist/${entityId}`, { method: "POST" });
}

export async function unwatchEntity(entityId: string) {
  await fetch(`${API_URL}/watchlist/${entityId}`, { method: "DELETE" });
}
