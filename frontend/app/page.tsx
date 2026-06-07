"use client";
import useSWR from "swr";
import BottleneckBoard from "@/components/BottleneckBoard";
import { SkeletonStatCard } from "@/components/ui/LoadingSkeleton";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { WatchlistPanel } from "@/components/WatchlistPanel";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

function HouseViewNarrative({ apiBase }: { apiBase: string }) {
  const { data, isLoading } = useSWR(`${apiBase}/house-view/narrative`, fetcher, {
    refreshInterval: 300000,
    revalidateOnFocus: false,
  });
  if (isLoading) return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6 animate-pulse">
      <div className="h-3 bg-slate-800 rounded w-40 mb-4" />
      <div className="space-y-2">
        <div className="h-3 bg-slate-800 rounded w-full" />
        <div className="h-3 bg-slate-800 rounded w-5/6" />
        <div className="h-3 bg-slate-800 rounded w-4/6" />
      </div>
    </div>
  );
  if (!data?.narrative) return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6 text-center">
      <p className="text-slate-500 text-sm">No house view overrides set. Add conviction calls above.</p>
    </div>
  );
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-semibold text-white">House View · Analyst Narrative</p>
        {data.cached && <span className="text-xs text-slate-500">cached</span>}
      </div>
      <div className="space-y-2">
        {data.narrative.split("\n\n").map((para: string, i: number) => (
          <p key={i} className="text-xs text-slate-300 leading-relaxed">{para}</p>
        ))}
      </div>
    </div>
  );
}

export default function Home() {
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const { data: regime, isLoading: regimeLoading } = useSWR(`${apiBase}/regime/`, fetcher, {
    refreshInterval: 60000,
    revalidateOnFocus: false,
  });
  const { data: graph, isLoading: graphLoading } = useSWR(`${apiBase}/graph/`, fetcher, {
    revalidateOnFocus: false,
  });

  const statCards = [
    { label: "Total Entities", value: graph?.nodes?.length?.toString(), loading: graphLoading },
    { label: "Active Claims", value: graph?.edges?.length?.toString(), loading: graphLoading },
    { label: "Current Regime", value: regime?.regime, loading: regimeLoading },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-1">Bottleneck Dashboard</h1>
      <p className="text-slate-400 text-sm mb-6">
        Ranked transmission bottlenecks across the US AI infrastructure stack
      </p>

      <div className="grid grid-cols-3 gap-4 mb-6">
        {statCards.map(({ label, value, loading }) =>
          loading ? (
            <SkeletonStatCard key={label} />
          ) : (
            <div key={label} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <p className="text-xs text-slate-400 mb-1">{label}</p>
              <p className="text-xl font-semibold text-white">{value ?? "—"}</p>
            </div>
          )
        )}
      </div>

      <HouseViewNarrative apiBase={apiBase} />
      <ErrorBoundary fallbackMessage="Bottleneck board failed to load">
        <BottleneckBoard limit={20} />
      </ErrorBoundary>
      <div className="mt-6">
        <WatchlistPanel />
      </div>
    </div>
  );
}
