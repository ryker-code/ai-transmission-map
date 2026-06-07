"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import type { GraphResponse, GraphNode, GraphEdge } from "@/lib/types";

export const ENTITY_COLORS: Record<string, string> = {
  semiconductor: "#6366f1",
  utility: "#f59e0b",
  hyperscaler: "#10b981",
  reit: "#8b5cf6",
  equipment: "#ef4444",
  financial: "#3b82f6",
  regulatory: "#6b7280",
  // legacy types
  public_co: "#6366f1",
  private_co: "#8b5cf6",
  asset: "#f59e0b",
  technology: "#3b82f6",
  geo: "#ec4899",
  market: "#64748b",
};

const EDGE_COLORS: Record<string, string> = {
  positive: "#10b981",
  bullish: "#10b981",
  negative: "#ef4444",
  bearish: "#ef4444",
  neutral: "#6b7280",
};

const LEGEND_TYPES = [
  { key: "semiconductor", label: "Semiconductor" },
  { key: "utility", label: "Utility" },
  { key: "hyperscaler", label: "Hyperscaler" },
  { key: "reit", label: "REIT" },
  { key: "equipment", label: "Equipment" },
  { key: "financial", label: "Financial" },
  { key: "regulatory", label: "Regulatory" },
];

interface Props {
  data: GraphResponse;
  onNodeClick?: (node: GraphNode) => void;
  watchedIds?: Set<string>;
  topBottleneckIds?: Set<string>;
  graphRef?: React.MutableRefObject<any>;
  onExport?: (type: "png" | "json", blob?: string) => void;
}

export default function TransmissionGraph({ data, onNodeClick, watchedIds, topBottleneckIds, graphRef, onExport }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [ForceGraph, setForceGraph] = useState<any>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [hoveredLink, setHoveredLink] = useState<any>(null);
  const [showLegend, setShowLegend] = useState(false);
  const internalRef = useRef<any>(null);
  const fgRef = graphRef ?? internalRef;

  useEffect(() => {
    import("react-force-graph-2d").then((mod) => {
      setForceGraph(() => mod.default);
    });
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setDimensions({ width: entry.contentRect.width, height: entry.contentRect.height });
      }
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const maxScore = Math.max(...data.nodes.map((n) => n.bottleneck_score ?? 0), 1);

  const graphData = {
    nodes: data.nodes.map((n) => {
      const score = n.bottleneck_score ?? 0;
      const size = 4 + (score / maxScore) * 20;
      return {
        id: n.id,
        label: n.label,
        entity_type: n.entity_type,
        sector: n.sector,
        bottleneck_score: score,
        color: ENTITY_COLORS[n.entity_type] ?? "#94a3b8",
        val: size,
        isWatched: watchedIds?.has(n.id),
        isTopBottleneck: topBottleneckIds?.has(n.id),
      };
    }),
    links: data.edges.map((e) => ({
      source: e.source,
      target: e.target,
      predicate: e.predicate,
      direction: e.direction,
      confidence: e.confidence ?? 0.7,
      horizon: (e as any).horizon ?? "12M",
      color: EDGE_COLORS[e.direction] ?? EDGE_COLORS.neutral,
      width: ((e.confidence ?? 0.7) * 3),
      curvature: 0.2,
    })),
  };

  const paintNode = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const r = node.val;
    const x = node.x;
    const y = node.y;

    // Pulsing glow for top bottleneck nodes
    if (node.isTopBottleneck) {
      const glow = 2 + Math.sin(Date.now() / 400) * 1.5;
      ctx.shadowColor = node.color;
      ctx.shadowBlur = r * glow;
      ctx.beginPath();
      ctx.arc(x, y, r + glow, 0, 2 * Math.PI);
      ctx.fillStyle = node.color + "40";
      ctx.fill();
      ctx.shadowBlur = 0;
    }

    // Node body
    ctx.beginPath();
    ctx.arc(x, y, r, 0, 2 * Math.PI);
    ctx.fillStyle = node.color;
    ctx.fill();

    // Gold ring for watched entities
    if (node.isWatched) {
      ctx.beginPath();
      ctx.arc(x, y, r + 2, 0, 2 * Math.PI);
      ctx.strokeStyle = "#f59e0b";
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Label at high zoom
    if (globalScale >= 1.5) {
      const fontSize = 10 / globalScale;
      ctx.font = `${fontSize}px Sans-Serif`;
      ctx.fillStyle = "#e2e8f0";
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      const label = node.label as string;
      ctx.fillText(label.length > 18 ? label.slice(0, 18) + "…" : label, x, y + r + 2);
    }
  }, []);

  const handleResetView = useCallback(() => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400, 40);
    }
  }, [fgRef]);

  const handleExportPng = useCallback(() => {
    const canvas = containerRef.current?.querySelector("canvas");
    if (!canvas) return;
    const url = canvas.toDataURL("image/png");
    const a = document.createElement("a");
    a.href = url;
    a.download = `transmission-graph-${Date.now()}.png`;
    a.click();
    if (onExport) onExport("png", url);
  }, [onExport]);

  const handleExportJson = useCallback(() => {
    const payload = {
      nodes: data.nodes,
      edges: data.edges,
      regime_filter: data.regime_tag ?? "ALL",
      exported_at: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `transmission-graph-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    if (onExport) onExport("json");
  }, [data, onExport]);

  if (!ForceGraph) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400 text-sm">
        Loading graph engine...
      </div>
    );
  }

  return (
    <div ref={containerRef} className="w-full h-full relative">
      <ForceGraph
        ref={fgRef}
        graphData={graphData}
        width={dimensions.width}
        height={dimensions.height}
        backgroundColor="#0f172a"
        nodeLabel={(n: any) => `${n.label} (${n.entity_type}) — score: ${n.bottleneck_score.toFixed(2)}`}
        nodeCanvasObject={paintNode}
        nodeCanvasObjectMode={() => "replace"}
        linkColor={(l: any) => l.color + "cc"}
        linkWidth={(l: any) => l.width}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        linkCurvature={(l: any) => l.curvature}
        linkLabel={(l: any) => `${l.predicate} — ${(l.confidence * 100).toFixed(0)}% conf — ${l.horizon}`}
        onLinkHover={setHoveredLink}
        onNodeClick={(node: any) => {
          if (onNodeClick) {
            onNodeClick({
              id: node.id,
              label: node.label,
              entity_type: node.entity_type,
              sector: node.sector,
              bottleneck_score: node.bottleneck_score,
            });
          }
        }}
        enableNodeDrag
        cooldownTicks={100}
      />

      {/* Controls panel — top-right overlay */}
      <div className="absolute top-3 right-3 flex flex-col gap-1.5 z-10">
        {/* Stats */}
        <div className="bg-slate-900/80 backdrop-blur border border-slate-700/60 rounded-lg px-3 py-1.5 text-xs text-slate-300">
          {graphData.nodes.length} nodes · {graphData.links.length} edges
        </div>

        {/* Reset View */}
        <button
          onClick={handleResetView}
          className="bg-slate-900/80 backdrop-blur border border-slate-700/60 rounded-lg px-3 py-1.5 text-xs text-slate-300 hover:text-white hover:border-slate-500 transition-colors text-left"
        >
          ⟳ Reset View
        </button>

        {/* Export PNG */}
        <button
          onClick={handleExportPng}
          className="bg-slate-900/80 backdrop-blur border border-slate-700/60 rounded-lg px-3 py-1.5 text-xs text-slate-300 hover:text-white hover:border-slate-500 transition-colors text-left"
        >
          ↓ Export PNG
        </button>

        {/* Export JSON */}
        <button
          onClick={handleExportJson}
          className="bg-slate-900/80 backdrop-blur border border-slate-700/60 rounded-lg px-3 py-1.5 text-xs text-slate-300 hover:text-white hover:border-slate-500 transition-colors text-left"
        >
          ↓ Export JSON
        </button>

        {/* Legend toggle */}
        <button
          onClick={() => setShowLegend((v) => !v)}
          className="bg-slate-900/80 backdrop-blur border border-slate-700/60 rounded-lg px-3 py-1.5 text-xs text-slate-300 hover:text-white hover:border-slate-500 transition-colors text-left"
        >
          {showLegend ? "▲ Hide Legend" : "▼ Show Legend"}
        </button>

        {/* Legend */}
        {showLegend && (
          <div className="bg-slate-900/90 backdrop-blur border border-slate-700/60 rounded-lg p-2.5 flex flex-col gap-1">
            {LEGEND_TYPES.map(({ key, label }) => (
              <div key={key} className="flex items-center gap-2">
                <span
                  className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: ENTITY_COLORS[key] }}
                />
                <span className="text-xs text-slate-300">{label}</span>
              </div>
            ))}
            <div className="mt-1 pt-1 border-t border-slate-700 flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: "#10b981" }} />
                <span className="text-xs text-slate-400">Bullish edge</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: "#ef4444" }} />
                <span className="text-xs text-slate-400">Bearish edge</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-0.5 rounded flex-shrink-0" style={{ backgroundColor: "#f59e0b", marginLeft: 1 }} />
                <span className="text-xs text-slate-400">Gold ring = watched</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Edge hover tooltip */}
      {hoveredLink && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-slate-800/90 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 pointer-events-none">
          {hoveredLink.predicate} · {(hoveredLink.confidence * 100).toFixed(0)}% · {hoveredLink.horizon}
        </div>
      )}
    </div>
  );
}
