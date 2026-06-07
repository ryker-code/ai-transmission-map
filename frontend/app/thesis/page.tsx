"use client";
import { useState } from "react";
import { api } from "@/lib/api-client";
import type { ThesisRunResponse } from "@/lib/types";

export default function ThesisPage() {
  const [thesis, setThesis] = useState("");
  const [depth, setDepth] = useState(2);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ThesisRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleRun() {
    if (thesis.length < 30) {
      setError("Thesis must be at least 30 characters.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.runThesis({ thesis, depth, include_private: true });
      setResult(res);
    } catch (e: any) {
      setError(e.message ?? "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold text-white mb-1">Thesis Workspace</h1>
      <p className="text-slate-400 text-sm mb-6">
        Interrogate your investment thesis against the transmission graph
      </p>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 mb-6">
        <label className="block text-sm text-slate-300 font-medium">Investment Thesis</label>
        <textarea
          value={thesis}
          onChange={(e) => setThesis(e.target.value)}
          placeholder="e.g. Transformer lead times will keep GE Vernova backlog elevated through 2026, supporting margin expansion and order visibility"
          className="w-full h-40 bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-sm text-white placeholder:text-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <div className="flex items-center gap-4">
          <label className="text-sm text-slate-400">Graph depth:</label>
          {[1, 2, 3, 4].map((d) => (
            <button
              key={d}
              onClick={() => setDepth(d)}
              className={`w-8 h-8 rounded-lg text-sm font-medium border transition-colors ${
                depth === d ? "bg-indigo-600 border-indigo-500 text-white" : "bg-slate-800 border-slate-700 text-slate-300"
              }`}
            >
              {d}
            </button>
          ))}
          <button
            onClick={handleRun}
            disabled={loading || thesis.length < 30}
            className="ml-auto px-5 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-indigo-500 transition-colors"
          >
            {loading ? "Analyzing..." : "Run Analysis"}
          </button>
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
      </div>

      {result && (
        <div className="space-y-4">
          {/* Score cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-900 border border-emerald-800/40 rounded-xl p-4">
              <p className="text-xs text-slate-400 mb-1">Support Score</p>
              <p className="text-2xl font-bold text-emerald-400">{(result.support_score * 100).toFixed(0)}%</p>
            </div>
            <div className="bg-slate-900 border border-red-800/40 rounded-xl p-4">
              <p className="text-xs text-slate-400 mb-1">Contradiction Score</p>
              <p className="text-2xl font-bold text-red-400">{(result.contradiction_score * 100).toFixed(0)}%</p>
            </div>
          </div>

          {/* Falsification triggers */}
          {result.falsification_triggers.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <p className="text-sm font-medium text-slate-300 mb-3">Falsification Triggers</p>
              <ul className="space-y-2">
                {result.falsification_triggers.map((t, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                    <span className="text-amber-400 mt-0.5">⚡</span>
                    {t}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Graph slice stats */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <p className="text-sm font-medium text-slate-300 mb-2">Graph Slice</p>
            <p className="text-sm text-slate-400">
              {result.graph_slice.nodes.length} nodes · {result.graph_slice.edges.length} edges analyzed
            </p>
            <p className="text-xs text-slate-500 mt-1">Run ID: {result.run_id}</p>
          </div>
        </div>
      )}
    </div>
  );
}
