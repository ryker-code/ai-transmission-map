"use client";

export function SkeletonCard({ className = "" }: { className?: string }) {
  return (
    <div className={`animate-pulse bg-slate-800 rounded-xl ${className}`} />
  );
}

export function SkeletonTable({ rows = 5 }: { rows?: number }) {
  return (
    <div className="animate-pulse space-y-2">
      <div className="h-4 bg-slate-800 rounded w-full" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-8 bg-slate-800/70 rounded w-full" />
      ))}
    </div>
  );
}

export function SkeletonGraph() {
  return (
    <div className="flex items-center justify-center w-full h-full bg-slate-900/50 rounded-xl">
      <div className="flex flex-col items-center gap-3">
        <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm text-slate-400">Initializing graph…</span>
      </div>
    </div>
  );
}

export function SkeletonStatCard() {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 animate-pulse">
      <div className="h-3 bg-slate-800 rounded w-24 mb-3" />
      <div className="h-8 bg-slate-800 rounded w-16" />
    </div>
  );
}
