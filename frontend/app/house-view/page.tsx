"use client";
import { useState } from "react";
import { api } from "@/lib/api-client";
import type { HouseViewUpdate } from "@/lib/types";

const CONVICTION_LEVELS = ["high", "medium", "low"] as const;

const CONVICTION_COLORS = {
  high: "bg-emerald-600 border-emerald-500",
  medium: "bg-amber-600 border-amber-500",
  low: "bg-slate-600 border-slate-500",
};

export default function HouseViewPage() {
  const [entityId, setEntityId] = useState("");
  const [weightOverride, setWeightOverride] = useState(1.0);
  const [conviction, setConviction] = useState<"high" | "medium" | "low">("medium");
  const [analystNote, setAnalystNote] = useState("");
  const [pinnedThesis, setPinnedThesis] = useState("");
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    if (!entityId.trim()) {
      setError("Entity ID is required.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await api.updateHouseView({
        entity_id: entityId,
        weight_override: weightOverride,
        conviction,
        analyst_note: analystNote || undefined,
        pinned_thesis: pinnedThesis || undefined,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e: any) {
      setError(e.message ?? "Update failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-white mb-1">House View</h1>
      <p className="text-slate-400 text-sm mb-6">
        Override bottleneck weights and annotate entities with analyst conviction
      </p>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-5">
        <div>
          <label className="block text-xs text-slate-400 mb-1">Entity ID</label>
          <input
            value={entityId}
            onChange={(e) => setEntityId(e.target.value)}
            placeholder="e.g. e0000001-0000-0000-0000-000000000057 (GE Vernova)"
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
          />
        </div>

        <div>
          <label className="block text-xs text-slate-400 mb-1">
            Weight Override: {weightOverride.toFixed(1)}x
            <span className="ml-2 text-slate-600">(0.1x = underweight, 1.0x = neutral, 3.0x = strong overweight)</span>
          </label>
          <input
            type="range"
            min={0.1}
            max={3.0}
            step={0.1}
            value={weightOverride}
            onChange={(e) => setWeightOverride(parseFloat(e.target.value))}
            className="w-full accent-indigo-500"
          />
        </div>

        <div>
          <label className="block text-xs text-slate-400 mb-2">Conviction</label>
          <div className="flex gap-2">
            {CONVICTION_LEVELS.map((level) => (
              <button
                key={level}
                onClick={() => setConviction(level)}
                className={`px-4 py-2 rounded-lg text-sm font-medium border capitalize transition-colors ${
                  conviction === level
                    ? `${CONVICTION_COLORS[level]} text-white`
                    : "bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-600"
                }`}
              >
                {level}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs text-slate-400 mb-1">Analyst Note (optional)</label>
          <textarea
            value={analystNote}
            onChange={(e) => setAnalystNote(e.target.value)}
            placeholder="Add context for this conviction override..."
            className="w-full h-24 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div>
          <label className="block text-xs text-slate-400 mb-1">Pinned Thesis Run ID (optional)</label>
          <input
            value={pinnedThesis}
            onChange={(e) => setPinnedThesis(e.target.value)}
            placeholder="run_id from Thesis Workspace..."
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
          />
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={handleSave}
            disabled={loading}
            className="px-5 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-medium disabled:opacity-40 hover:bg-indigo-500 transition-colors"
          >
            {loading ? "Saving..." : "Save House View"}
          </button>
          {saved && <span className="text-emerald-400 text-sm">✓ Saved</span>}
          {error && <span className="text-red-400 text-sm">{error}</span>}
        </div>
      </div>

      {/* Quick reference entity IDs */}
      <div className="mt-6 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <p className="text-xs font-medium text-slate-400 mb-3 uppercase tracking-wide">Key Entity IDs (seed data)</p>
        <div className="space-y-1.5 text-xs font-mono">
          {[
            ["GE Vernova", "e0000001-0000-0000-0000-000000000057"],
            ["Vertiv Holdings", "e0000001-0000-0000-0000-000000000053"],
            ["Constellation Energy", "e0000001-0000-0000-0000-000000000036"],
            ["Nvidia", "e0000001-0000-0000-0000-000000000016"],
            ["Dominion Energy", "e0000001-0000-0000-0000-000000000035"],
            ["NextEra Energy", "e0000001-0000-0000-0000-000000000034"],
          ].map(([name, id]) => (
            <div key={id} className="flex items-center gap-2">
              <button
                onClick={() => setEntityId(id)}
                className="text-indigo-400 hover:text-indigo-300 transition-colors text-left"
              >
                {name}
              </button>
              <span className="text-slate-600">{id}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
