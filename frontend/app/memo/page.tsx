"use client";
import { useState } from "react";
import { api } from "@/lib/api-client";
import type { MemoResponse } from "@/lib/types";

const STYLE_OPTIONS = [
  { value: "buyside_lp", label: "Buyside LP Note" },
  { value: "sellside_note", label: "Sellside Note" },
  { value: "internal_brief", label: "Internal Brief" },
] as const;

type MemoStyle = typeof STYLE_OPTIONS[number]["value"];

export default function MemoPage() {
  const [style, setStyle] = useState<MemoStyle>("buyside_lp");
  const [thesisRunId, setThesisRunId] = useState("");
  const [maxWords, setMaxWords] = useState(800);
  const [loading, setLoading] = useState(false);
  const [memo, setMemo] = useState<MemoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    if (!thesisRunId.trim()) {
      setError("Enter a thesis run ID (from Thesis Workspace).");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.generateMemo({ thesis_run_id: thesisRunId, style, max_words: maxWords });
      setMemo(res);
    } catch (e: any) {
      setError(e.message ?? "Memo generation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold text-white mb-1">Memo Generator</h1>
      <p className="text-slate-400 text-sm mb-6">Generate investor-style memos from thesis runs</p>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-5 mb-6">
        <div>
          <label className="block text-sm text-slate-300 font-medium mb-2">Thesis Run ID</label>
          <input
            type="text"
            value={thesisRunId}
            onChange={(e) => setThesisRunId(e.target.value)}
            placeholder="Paste run_id from Thesis Workspace..."
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div>
          <label className="block text-sm text-slate-300 font-medium mb-2">Style</label>
          <div className="flex gap-2">
            {STYLE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setStyle(opt.value)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                  style === opt.value
                    ? "bg-indigo-600 border-indigo-500 text-white"
                    : "bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-600"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="px-5 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-indigo-500 transition-colors"
          >
            {loading ? "Generating..." : "Generate Memo"}
          </button>
          <span className="text-xs text-slate-500">Full LLM generation wired — Day 2 Agent</span>
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
      </div>

      {memo && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-300">Memo Output</p>
            <div className="flex gap-2 text-xs text-slate-500">
              <span>Regime: {memo.regime}</span>
              <span>·</span>
              <span>Model: {memo.model_used}</span>
            </div>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-4 text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
            {memo.memo_text}
          </div>
          {memo.key_bottlenecks.length > 0 && (
            <div>
              <p className="text-xs text-slate-400 mb-1.5">Key Bottlenecks</p>
              <div className="flex flex-wrap gap-2">
                {memo.key_bottlenecks.map((b) => (
                  <span key={b} className="px-2 py-0.5 bg-amber-900/30 border border-amber-700/40 rounded text-xs text-amber-400">{b}</span>
                ))}
              </div>
            </div>
          )}
          <div className="pt-2 border-t border-slate-800">
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/memo/${memo.memo_id}/pdf`}
              download
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-sm text-white transition-colors"
            >
              ↓ Download PDF
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
