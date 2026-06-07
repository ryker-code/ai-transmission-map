"use client";
import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import type { EntityResponse } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function EntitySearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<EntityResponse[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!query.trim()) { setResults([]); setOpen(false); return; }
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/entities/?search=${encodeURIComponent(query)}&limit=6`);
        const data = await res.json();
        setResults(Array.isArray(data) ? data : []);
        setOpen(true);
      } catch { setResults([]); } finally { setLoading(false); }
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  function select(id: string) {
    setQuery(""); setResults([]); setOpen(false);
    router.push(`/entities/${id}`);
  }

  return (
    <div ref={ref} className="relative">
      <input
        type="text"
        placeholder="Search entities…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
      />
      {open && results.length > 0 && (
        <ul className="absolute z-50 top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl overflow-hidden">
          {results.map((e) => (
            <li key={e.id}>
              <button
                onClick={() => select(e.id)}
                className="w-full text-left px-3 py-2 hover:bg-slate-700 transition-colors"
              >
                <p className="text-xs font-medium text-white truncate">{e.canonical_name}</p>
                <p className="text-xs text-slate-400">{e.entity_type}{e.ticker ? ` · ${e.ticker}` : ""}</p>
              </button>
            </li>
          ))}
        </ul>
      )}
      {loading && (
        <p className="absolute right-2 top-2 text-xs text-slate-500 animate-pulse">…</p>
      )}
    </div>
  );
}
