"use client";
import { useState } from "react";
import { api } from "@/lib/api-client";
import type { EvidenceResponse } from "@/lib/types";

const SOURCE_TYPES = ["bloomberg", "sec", "utility_filing", "public"] as const;

export default function EvidencePage() {
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [sourceType, setSourceType] = useState<"bloomberg" | "sec" | "utility_filing" | "public">("bloomberg");
  const [note, setNote] = useState("");
  const [tags, setTags] = useState("");
  const [trustScore, setTrustScore] = useState(0.7);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<EvidenceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!url || !title || note.length < 20) {
      setError("URL, title, and note (20+ chars) are required.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.ingestEvidence({
        url,
        title,
        source_type: sourceType,
        analyst_note: note,
        tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
        trust_score: trustScore,
      });
      setResult(res);
    } catch (e: any) {
      setError(e.message ?? "Ingestion failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-white mb-1">Evidence Ingest</h1>
      <p className="text-slate-400 text-sm mb-6">
        Submit Bloomberg, SEC, or public notes to trigger the LangGraph extraction pipeline
      </p>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="block text-xs text-slate-400 mb-1">URL</label>
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div className="col-span-2">
            <label className="block text-xs text-slate-400 mb-1">Title</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Article or report title"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Source Type</label>
            <select
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value as any)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {SOURCE_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Tags (comma-separated)</label>
            <input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="transformers, grid, utilities"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs text-slate-400 mb-1">Analyst Note (min 20 chars)</label>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Summarize the key investment-relevant claims from this source..."
            className="w-full h-32 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="block text-xs text-slate-400 mb-1">Trust Score: {trustScore.toFixed(1)}</label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.1}
              value={trustScore}
              onChange={(e) => setTrustScore(parseFloat(e.target.value))}
              className="w-full accent-indigo-500"
            />
          </div>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="px-5 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-medium disabled:opacity-40 hover:bg-indigo-500 transition-colors"
          >
            {loading ? "Submitting..." : "Ingest Evidence"}
          </button>
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
      </div>

      {result && (
        <div className="mt-4 bg-slate-900 border border-emerald-800/40 rounded-xl p-4 space-y-2">
          <p className="text-sm font-medium text-emerald-400">✓ Evidence accepted — pipeline running</p>
          <p className="text-xs text-slate-400">Source ID: {result.source_id}</p>
          <p className="text-xs text-slate-400">Note ID: {result.note_id}</p>
          <p className="text-xs text-slate-400">Status: {result.status}</p>
          <p className="text-xs text-slate-500 mt-2">
            The Scout → Extractor → Resolver → Critic → Scorer pipeline is running in the background.
            Extracted entities and claims will appear in the Graph and Bottleneck Dashboard within seconds.
          </p>
        </div>
      )}
    </div>
  );
}
