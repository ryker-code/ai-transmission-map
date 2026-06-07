"use client";
// TODO: Wire "Run Analysis" button to POST /thesis/run and display ThesisRunResponse
import { useState } from "react";

export default function ThesisPage() {
  const [thesis, setThesis] = useState("");

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-1">Thesis Workspace</h1>
      <p className="text-slate-400 text-sm mb-6">
        Interrogate your investment thesis against the transmission graph
      </p>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <label className="block text-sm text-slate-300 font-medium">Investment Thesis</label>
        <textarea
          value={thesis}
          onChange={(e) => setThesis(e.target.value)}
          placeholder="Enter your investment thesis here... (e.g. Transformer lead times will keep GE Vernova backlog elevated through 2026, supporting margin expansion and order visibility)"
          className="w-full h-40 bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-sm text-white placeholder:text-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <div className="flex items-center gap-4">
          <button
            disabled
            className="px-5 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Run Analysis
          </button>
          <span className="text-xs text-slate-500">Wire to POST /thesis/run — Day 2</span>
        </div>
      </div>
    </div>
  );
}
