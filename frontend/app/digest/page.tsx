"use client";
import { useState } from "react";

const API_URL = '/api/proxy';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "dev-key-change-in-production";

export default function DigestPage() {
  const [loading, setLoading] = useState(false);
  const [digestText, setDigestText] = useState("");
  const [generatedAt, setGeneratedAt] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    setDigestText("");
    try {
      const resp = await fetch(`${API_URL}/digest/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Api-Key": API_KEY },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setDigestText(data.digest_text ?? "");
      setGeneratedAt(data.generated_at ?? "");
    } catch (e: any) {
      setError(e.message ?? "Failed to generate digest");
    } finally {
      setLoading(false);
    }
  }

  async function handleCopy() {
    await navigator.clipboard.writeText(digestText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  // Render basic markdown bold/headers
  function renderDigest(text: string) {
    return text.split("\n").map((line, i) => {
      if (line.startsWith("**") && line.endsWith("**")) {
        return (
          <p key={i} className="text-sm font-semibold text-white mt-4 mb-1">
            {line.replace(/\*\*/g, "")}
          </p>
        );
      }
      if (line.startsWith("# ")) {
        return (
          <p key={i} className="text-base font-bold text-indigo-300 mb-3">
            {line.slice(2)}
          </p>
        );
      }
      if (line.startsWith("  - ") || line.startsWith("  • ")) {
        return (
          <p key={i} className="text-xs text-slate-300 ml-4 leading-relaxed">
            {line.trimStart()}
          </p>
        );
      }
      if (line === "---") {
        return <hr key={i} className="border-slate-700 my-3" />;
      }
      return (
        <p key={i} className="text-sm text-slate-300 leading-relaxed">
          {line || " "}
        </p>
      );
    });
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold text-white mb-1">Weekly Digest</h1>
      <p className="text-slate-400 text-sm mb-6">
        Generate a professional weekly summary for LP distribution
      </p>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
        <p className="text-sm text-slate-300 mb-4">
          Aggregates regime, bottleneck movements, analyst conviction calls, and falsification alerts
          into a 400-word investor digest. Claude claude-opus-4-5 formats the output when API key is configured.
        </p>
        <div className="flex items-center gap-3">
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="px-5 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-indigo-500 transition-colors"
          >
            {loading ? "Generating…" : "Generate Digest"}
          </button>
          {generatedAt && (
            <span className="text-xs text-slate-500">
              Generated at {new Date(generatedAt).toLocaleTimeString()}
            </span>
          )}
        </div>
        {error && <p className="text-red-400 text-sm mt-3">{error}</p>}
      </div>

      {digestText && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
            <p className="text-sm font-semibold text-white">Weekly Digest Output</p>
            <div className="flex gap-2">
              <button
                onClick={handleCopy}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition-colors"
              >
                {copied ? "Copied ✓" : "Copy"}
              </button>
            </div>
          </div>
          <div className="px-5 py-5 space-y-0.5 font-mono text-xs leading-relaxed">
            {renderDigest(digestText)}
          </div>
        </div>
      )}
    </div>
  );
}
