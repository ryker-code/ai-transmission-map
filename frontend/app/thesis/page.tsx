"use client";
import { useState } from "react";
import { api } from "@/lib/api-client";
import type { ThesisRunResponse, ScenarioResponse } from "@/lib/types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const PRESET_SCENARIOS = [
  {
    name: "Transformer lead times normalize (52 weeks)",
    description: "Reduces confidence on transformer bottleneck claims by 0.4",
    claim_overrides: [
      { claim_id: "seed-0", confidence_override: 0.35 },
      { claim_id: "seed-1", confidence_override: 0.30 },
    ],
    entity_weight_overrides: [] as { entity_id: string; weight_override: number }[],
  },
  {
    name: "FERC fast-track interconnection approved",
    description: "Reduces grid interconnect confidence, increases utility beneficiary confidence",
    claim_overrides: [
      { claim_id: "seed-2", confidence_override: 0.40 },
      { claim_id: "seed-3", confidence_override: 0.45 },
    ],
    entity_weight_overrides: [] as { entity_id: string; weight_override: number }[],
  },
  {
    name: "Hyperscaler capex pause (−30%)",
    description: "Reduces confidence on GPU demand and datacenter build claims by 0.35",
    claim_overrides: [
      { claim_id: "seed-4", confidence_override: 0.35 },
      { claim_id: "seed-5", confidence_override: 0.40 },
    ],
    entity_weight_overrides: [] as { entity_id: string; weight_override: number }[],
  },
];

function DeltaBadge({ value }: { value: number }) {
  const sign = value >= 0 ? "+" : "";
  const color = value >= 0 ? "text-emerald-400" : "text-red-400";
  return <span className={`text-xs font-mono ${color}`}>{sign}{(value * 100).toFixed(1)}pp</span>;
}

export default function ThesisPage() {
  const [thesis, setThesis] = useState("");
  const [depth, setDepth] = useState(2);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ThesisRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<ScenarioResponse[]>([]);
  const [scenarioLoading, setScenarioLoading] = useState<string | null>(null);

  async function handleRun() {
    if (thesis.length < 30) {
      setError("Thesis must be at least 30 characters.");
      return;
    }
    setLoading(true);
    setError(null);
    setScenarios([]);
    try {
      const res = await api.runThesis({ thesis, depth, include_private: true });
      setResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  async function runScenario(preset: typeof PRESET_SCENARIOS[0]) {
    if (!result) return;
    setScenarioLoading(preset.name);
    try {
      const res = await fetch(`${API}/thesis/scenario`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          base_run_id: result.run_id,
          scenario_name: preset.name,
          claim_overrides: preset.claim_overrides,
          entity_weight_overrides: preset.entity_weight_overrides,
        }),
      });
      const data = await res.json() as ScenarioResponse;
      setScenarios((prev) => {
        const filtered = prev.filter((s) => s.scenario_name !== preset.name);
        return [...filtered, data];
      });
    } catch {
      // silently ignore
    } finally {
      setScenarioLoading(null);
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
          data-testid="thesis-text"
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
            data-testid="run-thesis"
            onClick={handleRun}
            disabled={loading || thesis.length < 30}
            className="ml-auto px-5 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-indigo-500 transition-colors"
          >
            {loading ? "Analyzing..." : "Run Analysis"}
          </button>
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        {loading && (
          <div className="pt-2 space-y-1.5">
            {[
              "BFS subgraph extraction",
              "Claim matching against graph",
              "Scoring & falsification analysis",
            ].map((step, i) => (
              <div key={step} className="flex items-center gap-2 text-xs text-slate-400">
                <span className={`w-3 h-3 rounded-full border ${
                  i === 0 ? "bg-indigo-500 border-indigo-400" :
                  i === 1 ? "border-indigo-500 animate-pulse" :
                  "border-slate-600"
                }`} />
                {step}
              </div>
            ))}
          </div>
        )}
      </div>

      {result && (
        <div className="space-y-4">
          {/* Score cards */}
          <div className="grid grid-cols-2 gap-4">
            <div data-testid="support-score" className="bg-slate-900 border border-emerald-800/40 rounded-xl p-4">
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

          {/* SCENARIO BRANCHING */}
          <div className="bg-slate-900 border border-indigo-800/40 rounded-xl p-5">
            <p className="text-sm font-semibold text-indigo-300 mb-1">What If? Scenario Workspace</p>
            <p className="text-xs text-slate-400 mb-4">
              Branch from this run with modified assumptions. Results are compared to base.
            </p>
            <div className="grid grid-cols-1 gap-3 mb-5">
              {PRESET_SCENARIOS.map((preset) => {
                const match = scenarios.find((s) => s.scenario_name === preset.name);
                return (
                  <div key={preset.name} className="bg-slate-800/60 rounded-lg p-4 border border-slate-700/60">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-white">{preset.name}</p>
                        <p className="text-xs text-slate-400 mt-0.5">{preset.description}</p>
                      </div>
                      <button
                        data-testid={preset.name.toLowerCase().includes("ferc") ? "scenario-ferc" : undefined}
                        onClick={() => runScenario(preset)}
                        disabled={scenarioLoading === preset.name}
                        className="shrink-0 px-3 py-1.5 rounded-lg bg-indigo-600/70 hover:bg-indigo-600 text-white text-xs font-medium transition-colors disabled:opacity-50"
                      >
                        {scenarioLoading === preset.name ? "Running…" : "Run Scenario"}
                      </button>
                    </div>

                    {match && (
                      <div data-testid="scenario-delta" className="mt-3 pt-3 border-t border-slate-700/60">
                        <div className="grid grid-cols-2 gap-3 mb-3">
                          <div>
                            <p className="text-xs text-slate-500 mb-1">Support</p>
                            <div className="flex items-center gap-2">
                              <span className="text-emerald-400 font-mono text-sm">{(result.support_score * 100).toFixed(1)}%</span>
                              <span className="text-slate-500 text-xs">→</span>
                              <span className="text-emerald-400 font-mono text-sm">{(match.support_score * 100).toFixed(1)}%</span>
                              <DeltaBadge value={match.delta_support} />
                            </div>
                          </div>
                          <div>
                            <p className="text-xs text-slate-500 mb-1">Contradiction</p>
                            <div className="flex items-center gap-2">
                              <span className="text-red-400 font-mono text-sm">{(result.contradiction_score * 100).toFixed(1)}%</span>
                              <span className="text-slate-500 text-xs">→</span>
                              <span className="text-red-400 font-mono text-sm">{(match.contradiction_score * 100).toFixed(1)}%</span>
                              <DeltaBadge value={match.delta_contradiction} />
                            </div>
                          </div>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed italic">{match.narrative}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
