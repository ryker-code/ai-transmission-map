"use client";

import { useEffect, useState } from "react";
import { Cpu, RefreshCw, CheckCircle, AlertCircle } from "lucide-react";
import type { ModelStatusEntry, ModelStatusResponse } from "@/lib/types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function getModelColor(name: string): string {
  if (name.includes("gemini")) return "bg-blue-900/40 text-blue-300 border-blue-700/40";
  if (name.includes("claude")) return "bg-violet-900/40 text-violet-300 border-violet-700/40";
  if (name.includes("whisper")) return "bg-amber-900/40 text-amber-300 border-amber-700/40";
  return "bg-slate-700/40 text-slate-300 border-slate-600/40";
}

function SuccessBar({ rate }: { rate: number }) {
  const pct = Math.round(rate * 100);
  const color = rate >= 0.9 ? "bg-emerald-500" : rate >= 0.7 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 w-10 text-right">{pct}%</span>
    </div>
  );
}

export default function ModelsPage() {
  const [data, setData] = useState<ModelStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchData = async () => {
    try {
      const res = await fetch(`${API}/models/status`);
      if (res.ok) {
        const json = await res.json();
        setData(json as ModelStatusResponse);
        setLastRefresh(new Date());
      }
    } catch {
      // silently skip on network error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30_000);
    return () => clearInterval(interval);
  }, []);

  const totalCalls = data?.models.reduce((s, m) => s + m.call_count, 0) ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-indigo-400" /> Model Attribution
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Per-model call counts, latency, and success rates — live log from pipeline
          </p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm text-slate-300 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* Summary row */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Total API Calls", value: totalCalls.toLocaleString() },
          { label: "Active Models", value: data?.models.filter((m) => m.call_count > 0).length ?? 0 },
          { label: "Last Updated", value: lastRefresh ? lastRefresh.toLocaleTimeString() : "—" },
        ].map(({ label, value }) => (
          <div key={label} className="bg-slate-900 rounded-xl border border-slate-800 p-4">
            <div className="text-xs text-slate-400 uppercase tracking-wide">{label}</div>
            <div className="text-2xl font-bold text-white mt-1">{value}</div>
          </div>
        ))}
      </div>

      {/* Table */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800">
              <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wide">Model</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wide">Tasks</th>
              <th className="text-right px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wide">Calls</th>
              <th className="text-right px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wide">Avg Latency</th>
              <th className="px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wide min-w-36">Success Rate</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                  Loading model stats…
                </td>
              </tr>
            )}
            {!loading && (!data || data.models.length === 0) && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                  No model calls logged yet. Ingest evidence to begin.
                </td>
              </tr>
            )}
            {data?.models.map((model: ModelStatusEntry) => (
              <tr key={model.name} className="border-b border-slate-800/60 hover:bg-slate-800/30 transition-colors">
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs border ${getModelColor(model.name)}`}>
                    {model.call_count > 0 ? (
                      <CheckCircle className="w-3 h-3" />
                    ) : (
                      <AlertCircle className="w-3 h-3 opacity-50" />
                    )}
                    {model.name}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {model.task_types.slice(0, 3).map((t) => (
                      <span key={t} className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 text-xs">
                        {t.replace(/_/g, " ")}
                      </span>
                    ))}
                    {model.task_types.length > 3 && (
                      <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-500 text-xs">
                        +{model.task_types.length - 3}
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-right font-mono text-white">
                  {model.call_count.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right text-slate-300 font-mono">
                  {model.call_count > 0 ? `${model.avg_latency_ms}ms` : "—"}
                </td>
                <td className="px-4 py-3">
                  <SuccessBar rate={model.success_rate} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-600">
        Auto-refreshes every 30s. Call log: <code className="text-slate-500">backend/db/model_call_log.jsonl</code>
      </p>
    </div>
  );
}
