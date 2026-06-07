"use client";
import { useState, useRef } from "react";
import { api } from "@/lib/api-client";
import type { EvidenceResponse } from "@/lib/types";

const SOURCE_TYPES = ["bloomberg", "sec", "utility_filing", "public"] as const;
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function EvidencePage() {
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [sourceType, setSourceType] = useState<"bloomberg" | "sec" | "utility_filing" | "public">("bloomberg");
  const [note, setNote] = useState("");
  const [tags, setTags] = useState("");
  const [trustScore, setTrustScore] = useState(0.7);
  const [loading, setLoading] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [result, setResult] = useState<EvidenceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [parsedEntities, setParsedEntities] = useState<string[]>([]);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageContext, setImageContext] = useState("");
  const [imageResult, setImageResult] = useState<any>(null);
  const [imageLoading, setImageLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [voiceContext, setVoiceContext] = useState("");
  const [voiceResult, setVoiceResult] = useState<any>(null);
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioFileRef = useRef<HTMLInputElement>(null);

  async function handleParseUrl() {
    if (!url) { setError("Enter a URL first."); return; }
    setParsing(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/evidence/parse-url?url=${encodeURIComponent(url)}`);
      const data = await res.json();
      if (data.title) setTitle(data.title);
      if (data.topic_tags?.length) {
        const newTags = data.topic_tags.join(", ");
        setTags((prev) => prev ? `${prev}, ${newTags}` : newTags);
      }
      if (data.detected_entities?.length) setParsedEntities(data.detected_entities);
      setSourceType(data.source_type === "bloomberg" ? "bloomberg" : sourceType);
    } catch (e: any) {
      setError("URL parse failed: " + (e.message ?? "unknown error"));
    } finally {
      setParsing(false);
    }
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach((t) => t.stop());
      };
      mr.start();
      mediaRecorderRef.current = mr;
      setRecording(true);
    } catch (e: any) {
      setError("Microphone access denied: " + (e.message ?? "check browser permissions"));
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  }

  async function handleVoiceUpload(blob: Blob, filename: string) {
    if (!voiceContext) { setError("Enter analyst context before uploading voice."); return; }
    setVoiceLoading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("audio", blob, filename);
      form.append("analyst_context", voiceContext);
      const res = await fetch(`${API_BASE}/evidence/voice`, { method: "POST", body: form });
      const data = await res.json();
      setVoiceResult(data);
    } catch (e: any) {
      setError("Voice upload failed: " + (e.message ?? "unknown error"));
    } finally {
      setVoiceLoading(false);
    }
  }

  async function handleImageUpload() {
    if (!imageFile || !imageContext) { setError("Select an image and enter context."); return; }
    setImageLoading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("image", imageFile);
      form.append("analyst_context", imageContext);
      const res = await fetch(`${API_BASE}/evidence/image`, { method: "POST", body: form });
      const data = await res.json();
      setImageResult(data);
    } catch (e: any) {
      setError("Image upload failed: " + (e.message ?? "unknown error"));
    } finally {
      setImageLoading(false);
    }
  }

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
            <div className="flex gap-2">
              <input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://bloomberg.com/..."
                className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <button
                onClick={handleParseUrl}
                disabled={parsing || !url}
                className="px-3 py-2 rounded-lg bg-slate-700 text-slate-200 text-xs font-medium disabled:opacity-40 hover:bg-slate-600 transition-colors whitespace-nowrap"
              >
                {parsing ? "Parsing..." : "Parse URL"}
              </button>
            </div>
            {parsedEntities.length > 0 && (
              <p className="text-xs text-indigo-400 mt-1">
                Detected entities: {parsedEntities.join(", ")}
              </p>
            )}
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

      {/* Image upload section */}
      <div className="mt-6 bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="text-base font-semibold text-white">Upload Chart / Slide</h2>
        <p className="text-xs text-slate-400">
          Extract transmission claims from a PNG/JPG chart or presentation slide via Claude vision.
        </p>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Image File (PNG or JPEG)</label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".png,.jpg,.jpeg"
            onChange={(e) => setImageFile(e.target.files?.[0] ?? null)}
            className="block text-sm text-slate-300 file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:bg-slate-700 file:text-slate-200 hover:file:bg-slate-600"
          />
          {imageFile && <p className="text-xs text-slate-500 mt-1">{imageFile.name} ({(imageFile.size / 1024).toFixed(0)} KB)</p>}
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Analyst Context (required)</label>
          <textarea
            value={imageContext}
            onChange={(e) => setImageContext(e.target.value)}
            placeholder="Describe what this chart depicts — e.g. 'Q3 2024 US power transformer lead times by vendor'"
            className="w-full h-20 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <button
          onClick={handleImageUpload}
          disabled={imageLoading || !imageFile || !imageContext}
          className="px-5 py-2 rounded-lg bg-violet-600 text-white text-sm font-medium disabled:opacity-40 hover:bg-violet-500 transition-colors"
        >
          {imageLoading ? "Extracting..." : "Extract Claims from Image"}
        </button>
        {imageResult && (
          <div className="bg-slate-800 rounded-lg p-3 space-y-1">
            <p className="text-xs text-emerald-400 font-medium">
              {imageResult.claims_accepted ?? 0} claims accepted from {imageResult.claims_extracted ?? 0} extracted
            </p>
            {imageResult.claims?.map((c: any, i: number) => (
              <p key={i} className="text-xs text-slate-400">
                {c.subject} —{c.predicate}→ {c.object} ({c.direction}, {(c.confidence * 100).toFixed(0)}%)
              </p>
            ))}
            {imageResult.error && <p className="text-xs text-red-400">{imageResult.error}</p>}
          </div>
        )}
      </div>

      {/* Voice note section */}
      <div className="mt-6 bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="text-base font-semibold text-white">Record Voice Note</h2>
        <p className="text-xs text-slate-400">
          Speak your analyst note — Whisper transcribes it, Claude extracts claims.
        </p>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Analyst Context (required)</label>
          <textarea
            value={voiceContext}
            onChange={(e) => setVoiceContext(e.target.value)}
            placeholder="What topic is this voice note about? e.g. 'Transformer supply chain bottlenecks Q4 2024'"
            className="w-full h-16 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div className="flex items-center gap-3">
          {!recording ? (
            <button onClick={startRecording} disabled={voiceLoading}
              className="px-4 py-2 rounded-lg bg-red-700 text-white text-sm font-medium hover:bg-red-600 disabled:opacity-40 transition-colors flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-300 inline-block" /> Record
            </button>
          ) : (
            <button onClick={stopRecording}
              className="px-4 py-2 rounded-lg bg-red-500 text-white text-sm font-medium hover:bg-red-400 animate-pulse transition-colors">
              Stop Recording
            </button>
          )}
          {audioBlob && (
            <button onClick={() => handleVoiceUpload(audioBlob, "recording.webm")} disabled={voiceLoading || !voiceContext}
              className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium disabled:opacity-40 hover:bg-indigo-500 transition-colors">
              {voiceLoading ? "Processing..." : "Extract Claims"}
            </button>
          )}
          <span className="text-xs text-slate-500">or</span>
          <input ref={audioFileRef} type="file" accept=".mp3,.wav,.m4a,.webm,.mp4"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) { setAudioBlob(f); setAudioUrl(URL.createObjectURL(f)); }
            }}
            className="hidden" />
          <button onClick={() => audioFileRef.current?.click()}
            className="px-3 py-1.5 rounded bg-slate-700 text-slate-300 text-xs hover:bg-slate-600 transition-colors">
            Upload file
          </button>
        </div>
        {audioUrl && (
          <audio controls src={audioUrl} className="w-full h-8" />
        )}
        {voiceResult && (
          <div className="bg-slate-800 rounded-lg p-3 space-y-1">
            <p className="text-xs text-emerald-400 font-medium">
              {voiceResult.claims_accepted ?? 0} claims accepted
            </p>
            {voiceResult.transcript && (
              <p className="text-xs text-slate-500 italic">&ldquo;{voiceResult.transcript}&rdquo;</p>
            )}
            {voiceResult.claims?.map((c: any, i: number) => (
              <p key={i} className="text-xs text-slate-400">
                {c.subject} —{c.predicate}→ {c.object}
              </p>
            ))}
            {voiceResult.error && <p className="text-xs text-red-400">{voiceResult.error}</p>}
          </div>
        )}
      </div>

      {result && (
        <div className="mt-4 bg-slate-900 border border-emerald-800/40 rounded-xl p-4 space-y-2">
          <p className="text-sm font-medium text-emerald-400">Evidence accepted — pipeline running</p>
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
