"use client";
import { useEffect, useRef, useState } from "react";
import type { GraphResponse, GraphNode, GraphEdge } from "@/lib/types";

const ENTITY_COLORS: Record<string, string> = {
  public_co: "#6366f1",
  private_co: "#8b5cf6",
  utility: "#10b981",
  asset: "#f59e0b",
  technology: "#3b82f6",
  geo: "#ec4899",
  market: "#64748b",
};

interface Props {
  data: GraphResponse;
  onNodeClick?: (node: GraphNode) => void;
}

export default function TransmissionGraph({ data, onNodeClick }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [ForceGraph, setForceGraph] = useState<any>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    // Dynamic import to avoid SSR issues with react-force-graph-2d
    import("react-force-graph-2d").then((mod) => {
      setForceGraph(() => mod.default);
    });
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const graphData = {
    nodes: data.nodes.map((n) => ({
      id: n.id,
      label: n.label,
      entity_type: n.entity_type,
      sector: n.sector,
      bottleneck_score: n.bottleneck_score,
      color: ENTITY_COLORS[n.entity_type] ?? "#64748b",
      val: n.bottleneck_score ? n.bottleneck_score * 10 + 3 : 3,
    })),
    links: data.edges.map((e) => ({
      source: e.source,
      target: e.target,
      predicate: e.predicate,
      direction: e.direction,
      confidence: e.confidence,
      color: e.direction === "positive" ? "#10b98180" : "#ef444480",
      curvature: 0.2,
    })),
  };

  if (!ForceGraph) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400 text-sm">
        Loading graph engine...
      </div>
    );
  }

  return (
    <div ref={containerRef} className="w-full h-full">
      <ForceGraph
        graphData={graphData}
        width={dimensions.width}
        height={dimensions.height}
        backgroundColor="#0f172a"
        nodeLabel={(n: any) => `${n.label} (${n.entity_type})`}
        nodeColor={(n: any) => n.color}
        nodeVal={(n: any) => n.val}
        linkColor={(l: any) => l.color}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        linkCurvature={(l: any) => l.curvature}
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
        nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
          const label = node.label as string;
          const fontSize = 12 / globalScale;
          ctx.font = `${fontSize}px Sans-Serif`;
          ctx.fillStyle = node.color;
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.val, 0, 2 * Math.PI);
          ctx.fill();
          if (globalScale >= 1.5) {
            ctx.fillStyle = "#e2e8f0";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(
              label.length > 20 ? label.slice(0, 20) + "…" : label,
              node.x,
              node.y + node.val + fontSize
            );
          }
        }}
      />
    </div>
  );
}
