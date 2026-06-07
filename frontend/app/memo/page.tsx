"use client";
// TODO: Wire "Generate Memo" to POST /memo/generate and render MemoResponse.memo_text
import { useState } from "react";

const STYLE_OPTIONS = [
  { value: "buyside_lp", label: "Buyside LP Note" },
  { value: "sellside_note", label: "Sellside Note" },
  { value: "internal_brief", label: "Internal Brief" },
] as const;

type MemoStyle = typeof STYLE_OPTIONS[number]["value"];

export default function MemoPage() {
  const [style, setStyle] = useState<MemoStyle>("buyside_lp");
  const [memoOutput, setMemoOutput] = useState("");

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-1">Memo Generator</h1>
      <p className="text-slate-400 text-sm mb-6">
        Generate investor-style memos from thesis runs
      </p>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-5">
        <div>
          <label className="block text-sm text-slate-300 font-medium mb-2">Memo Style</label>
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
            disabled
            className="px-5 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Generate Memo
          </button>
          <span className="text-xs text-slate-500">Wire to POST /memo/generate — Day 2</span>
        </div>

        <div>
          <label className="block text-sm text-slate-300 font-medium mb-2">Memo Output</label>
          <div className="min-h-48 bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-sm text-slate-500">
            {memoOutput || "Memo output will appear here after generation..."}
          </div>
        </div>
      </div>
    </div>
  );
}
