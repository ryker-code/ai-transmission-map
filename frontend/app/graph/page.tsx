"use client";
import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import dynamic from "next/dynamic";
import type { GraphResponse, GraphNode } from "@/lib/types";

const API_BASE = '/api/proxy';
const fetcher = (url: string) => fetch(url).then((r) => r.json());

// Dynamic import avoids SSR crash (react-force-graph-2d needs window)
const TransmissionGraph = dynamic(() => import("@/components/TransmissionGraph"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full text-slate-400 text-sm">
      Loading graph engine...
    </div>
  ),
});

export default function GraphPage() {
  const [selectedRegime, setSelectedRegime] = useState<string>("");
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const url = selectedRegime
    ? `${API_BASE}/graph/?regime=${selectedRegime}`
    : `${API_BASE}/graph/`;

  const { data, isLoading } = useSWR<GraphResponse>(url, fetcher);

  const regimes = [
    "AI_CAPEX_EXPANSION",
    "SUPPLY_CHAIN_STRESS",
    "GRID_BOTTLENECK",
    "POWER_PRICE_SPREAD",
    "REGULATORY",
  ];

  return (
    <div className="h-full flex flex-col gap-4">
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">Transmission Graph Explorer</h1>
          <p className="text-slate-400 text-sm">
            {data ? `${data.nodes.length} nodes · ${data.edges.length} edges` : "Force-directed view of AI infrastructure dependencies"}
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-indigo-900/40 border border-indigo-700/40 text-xs text-indigo-300">
          {data?.regime_tag ?? "AI_CAPEX_EXPANSION"}
        </span>
      </div>

      {/* Regime filter pills */}
      <div className="flex gap-2 flex-wrap flex-shrink-0">
        <button
          onClick={() => setSelectedRegime("")}
          className={`px-3 py-1 rounded-full text-xs border transition-colors ${
            !selectedRegime ? "bg-indigo-600 border-indigo-500 text-white" : "bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-600"
          }`}
        >
          All
        </button>
        {regimes.map((r) => (
          <button
            key={r}
            onClick={() => setSelectedRegime(r === selectedRegime ? "" : r)}
            className={`px-3 py-1 rounded-full text-xs border transition-colors ${
              selectedRegime === r ? "bg-indigo-600 border-indigo-500 text-white" : "bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-600"
            }`}
          >
            {r.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      <div className="flex flex-1 gap-4 min-h-0">
        <div className="flex-1 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center h-full text-slate-400 text-sm">
              Loading graph...
            </div>
          ) : data ? (
            <TransmissionGraph data={data} onNodeClick={setSelectedNode} />
          ) : (
            <div className="flex items-center justify-center h-full text-slate-500 text-sm">
              Could not load graph — ensure backend is running on port 8000.
            </div>
          )}
        </div>

        {/* Node detail panel */}
        {selectedNode && (
          <div className="w-64 bg-slate-900 border border-slate-800 rounded-xl p-4 flex-shrink-0">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-slate-400 font-medium uppercase tracking-wide">Node Detail</span>
              <button onClick={() => setSelectedNode(null)} className="text-slate-500 hover:text-white text-xs">✕</button>
            </div>
            <p className="text-white font-semibold text-sm mb-1">{selectedNode.label}</p>
            <p className="text-slate-400 text-xs mb-3">{selectedNode.entity_type}</p>
            {selectedNode.sector && (
              <p className="text-slate-500 text-xs">{selectedNode.sector}</p>
            )}
            {selectedNode.bottleneck_score != null && (
              <div className="mt-3 pt-3 border-t border-slate-800">
                <p className="text-xs text-slate-400">Bottleneck Score</p>
                <p className="text-lg font-bold text-indigo-400">{selectedNode.bottleneck_score.toFixed(3)}</p>
              </div>
            )}
            <div className="mt-3 pt-3 border-t border-slate-800">
              <Link
                href={`/entities/${selectedNode.id}`}
                className="text-xs text-indigo-400 hover:text-indigo-300"
              >
                View full detail →
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
