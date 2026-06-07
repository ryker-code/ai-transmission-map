"use client";
import { useState, useRef } from "react";
import { api } from "@/lib/api-client";
import type { MemoResponse } from "@/lib/types";

const STYLE_OPTIONS = [
  { value: "buyside_lp", label: "Buyside LP Note" },
  { value: "sellside_note", label: "Sellside Note" },
  { value: "internal_brief", label: "Internal Brief" },
] as const;

type MemoStyle = typeof STYLE_OPTIONS[number]["value"];

const API_URL = '/api/proxy';

export default function MemoPage() {
  const [style, setStyle] = useState<MemoStyle>("buyside_lp");
  const [thesisRunId, setThesisRunId] = useState("");
  const [maxWords, setMaxWords] = useState(800);
  const [streamMode, setStreamMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [memo, setMemo] = useState<MemoResponse | null>(null);
  const [streamText, setStreamText] = useState("");
  const [streamTokens, setStreamTokens] = useState(0);
  const [streamDone, setStreamDone] = useState(false);
  const [streamMemoId, setStreamMemoId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  async function handleGenerate() {
    if (!thesisRunId.trim()) {
      setError("Enter a thesis run ID (from Thesis Workspace).");
      return;
    }
    setError(null);

    if (streamMode) {
      await handleStream();
    } else {
      await handleBatch();
    }
  }

  async function handleBatch() {
    setLoading(true);
    setMemo(null);
    try {
      const res = await api.generateMemo({ thesis_run_id: thesisRunId, style, max_words: maxWords });
      setMemo(res);
    } catch (e: any) {
      setError(e.message ?? "Memo generation failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleStream() {
    setLoading(true);
    setStreamText("");
    setStreamTokens(0);
    setStreamDone(false);
    setStreamMemoId(null);

    abortRef.current = new AbortController();

    try {
      const resp = await fetch(`${API_URL}/memo/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thesis_run_id: thesisRunId, style, max_words: maxWords }),
        signal: abortRef.current.signal,
      });

      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      if (!resp.body) throw new Error("No response body");

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });

        const lines = buf.split("\n\n");
        buf = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const payload = JSON.parse(line.slice(6));
            if (payload.done) {
              setStreamDone(true);
              setStreamMemoId(payload.memo_id ?? null);
            } else if (payload.chunk) {
              setStreamText((prev) => prev + payload.chunk);
              setStreamTokens(payload.tokens ?? 0);
            } else if (payload.error) {
              setError(payload.error);
            }
          } catch {
            // skip malformed lines
          }
        }
      }
    } catch (e: any) {
      if (e.name !== "AbortError") setError(e.message ?? "Stream failed");
    } finally {
      setLoading(false);
    }
  }

  const displayText = streamMode ? streamText : memo?.memo_text ?? "";
  const memoId = streamMode ? streamMemoId : memo?.memo_id ?? null;

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
          <div className="flex gap-2 flex-wrap">
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

        <div className="flex items-center gap-3">
          <button
            data-testid="stream-toggle"
            onClick={() => setStreamMode((v) => !v)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              streamMode
                ? "bg-emerald-700 border-emerald-600 text-white"
                : "bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600"
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${streamMode ? "bg-emerald-300 animate-pulse" : "bg-slate-500"}`} />
            {streamMode ? "Stream ON" : "Stream OFF"}
          </button>
          <span className="text-xs text-slate-500">Stream mode shows tokens as they arrive</span>
        </div>

        <div className="flex items-center gap-4">
          <button
            data-testid="generate-memo"
            onClick={handleGenerate}
            disabled={loading}
            className="px-5 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-indigo-500 transition-colors"
          >
            {loading
              ? streamMode
                ? `Streaming… ${streamTokens} tokens`
                : "Generating…"
              : streamMode
              ? "Stream Memo"
              : "Generate Memo"}
          </button>
          {loading && streamMode && (
            <button
              onClick={() => abortRef.current?.abort()}
              className="px-3 py-2 rounded-lg bg-slate-700 text-sm text-slate-300 hover:bg-slate-600 transition-colors"
            >
              Stop
            </button>
          )}
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
      </div>

      {(displayText || (streamMode && loading)) && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-300">
              {streamMode ? "Live Output" : "Memo Output"}
            </p>
            <div className="flex gap-2 text-xs text-slate-500">
              {streamMode && streamTokens > 0 && <span>{streamTokens} tokens</span>}
              {!streamMode && memo && (
                <>
                  <span>Regime: {memo.regime}</span>
                  <span>·</span>
                  <span>Model: {memo.model_used}</span>
                </>
              )}
            </div>
          </div>

          <div data-testid="memo-text" className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-4 text-sm text-slate-200 whitespace-pre-wrap leading-relaxed min-h-[120px]">
            {displayText}
            {streamMode && loading && (
              <span data-testid="memo-cursor" className="inline-block w-0.5 h-4 bg-indigo-400 ml-0.5 animate-pulse align-middle" />
            )}
          </div>

          {!streamMode && memo?.key_bottlenecks && memo.key_bottlenecks.length > 0 && (
            <div>
              <p className="text-xs text-slate-400 mb-1.5">Key Bottlenecks</p>
              <div className="flex flex-wrap gap-2">
                {memo.key_bottlenecks.map((b) => (
                  <span key={b} className="px-2 py-0.5 bg-amber-900/30 border border-amber-700/40 rounded text-xs text-amber-400">{b}</span>
                ))}
              </div>
            </div>
          )}

          {memoId && (!streamMode || streamDone) && (
            <div className="pt-2 border-t border-slate-800">
              <a
                href={`${API_URL}/memo/${memoId}/pdf`}
                download
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-sm text-white transition-colors"
              >
                ↓ Download PDF
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
