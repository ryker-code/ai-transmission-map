"use client";
import useSWR from "swr";
import type { RegimeTimelineResponse, RegimeTimelineEntry } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const fetcher = (url: string) => fetch(url).then((r) => r.json());

const REGIME_COLORS: Record<string, string> = {
  AI_CAPEX_EXPANSION: "bg-indigo-600",
  SUPPLY_CHAIN_STRESS: "bg-amber-600",
  GRID_BOTTLENECK: "bg-rose-600",
  POWER_PRICE_SPREAD: "bg-orange-600",
  REGULATORY: "bg-violet-600",
};

const REGIME_TEXT: Record<string, string> = {
  AI_CAPEX_EXPANSION: "text-indigo-400",
  SUPPLY_CHAIN_STRESS: "text-amber-400",
  GRID_BOTTLENECK: "text-rose-400",
  POWER_PRICE_SPREAD: "text-orange-400",
  REGULATORY: "text-violet-400",
};

function ConfidenceBar({ confidence, regime }: { confidence: number; regime: string }) {
  const color = REGIME_COLORS[regime] ?? "bg-slate-600";
  return (
    <div className="w-full bg-slate-800 rounded-full h-2">
      <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${confidence * 100}%` }} />
    </div>
  );
}

function RegimeTimeline({ entries }: { entries: RegimeTimelineEntry[] }) {
  const recent = entries.slice(-14);
  const segmented: { regime: string; count: number; start: string }[] = [];
  for (const e of recent) {
    const last = segmented[segmented.length - 1];
    if (last && last.regime === e.regime_tag) { last.count++; }
    else { segmented.push({ regime: e.regime_tag, count: 1, start: e.timestamp }); }
  }
  const total = recent.length;
  return (
    <div className="flex w-full h-6 rounded-lg overflow-hidden gap-0.5">
      {segmented.map((s, i) => (
        <div
          key={i}
          title={`${s.regime}: ${s.count} days`}
          className={`${REGIME_COLORS[s.regime] ?? "bg-slate-600"} opacity-80 hover:opacity-100 transition-opacity`}
          style={{ width: `${(s.count / total) * 100}%` }}
        />
      ))}
    </div>
  );
}

export default function RegimePage() {
  const { data, isLoading, error } = useSWR<RegimeTimelineResponse>(
    `${API_BASE}/regime/timeline`,
    fetcher,
    { refreshInterval: 60000 }
  );

  const currentRegime = data?.current_regime ?? "";

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Regime Timeline</h1>
        <p className="text-slate-400 text-sm">30-day market regime signal evolution · confidence-weighted</p>
      </div>

      {isLoading && <p className="text-slate-400 text-sm animate-pulse">Loading timeline…</p>}
      {error && <p className="text-red-400 text-sm">Could not load regime timeline.</p>}

      {data && (
        <>
          {/* Current regime banner */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-400 mb-1">Current Regime</p>
              <p className={`text-xl font-bold ${REGIME_TEXT[currentRegime] ?? "text-white"}`}>
                {currentRegime.replace(/_/g, " ")}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-slate-400 mb-1">Latest Confidence</p>
              <p className="text-xl font-bold text-white">
                {((data.entries[data.entries.length - 1]?.confidence ?? 0) * 100).toFixed(0)}%
              </p>
            </div>
          </div>

          {/* 14-day band chart */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <p className="text-xs text-slate-400 mb-3">14-Day Regime Band</p>
            <RegimeTimeline entries={data.entries} />
            <div className="flex flex-wrap gap-3 mt-3">
              {Object.entries(REGIME_COLORS).map(([r, color]) => (
                <span key={r} className="flex items-center gap-1.5 text-xs text-slate-400">
                  <span className={`w-2 h-2 rounded-sm ${color} opacity-80`} />
                  {r.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          </div>

          {/* Timeline table */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <p className="text-xs text-slate-400 mb-3">30-Day Signal Log</p>
            <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
              {[...data.entries].reverse().map((e, i) => (
                <div key={i} className="flex items-center gap-3">
                  <span className="text-xs text-slate-500 w-20 flex-shrink-0">
                    {e.timestamp.slice(0, 10)}
                  </span>
                  <span className={`text-xs font-medium w-48 flex-shrink-0 ${REGIME_TEXT[e.regime_tag] ?? "text-slate-300"}`}>
                    {e.regime_tag.replace(/_/g, " ")}
                  </span>
                  <div className="flex-1">
                    <ConfidenceBar confidence={e.confidence} regime={e.regime_tag} />
                  </div>
                  <span className="text-xs text-slate-400 w-10 text-right flex-shrink-0">
                    {(e.confidence * 100).toFixed(0)}%
                  </span>
                  <span className="text-xs text-slate-600 w-16 text-right flex-shrink-0">
                    {e.dominant_claim_count} claims
                  </span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
