"use client";
import useSWR from "swr";
import BottleneckBoard from "@/components/BottleneckBoard";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function Home() {
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const { data: regime } = useSWR(`${apiBase}/regime/`, fetcher, {
    refreshInterval: 60000,
  });
  const { data: graph } = useSWR(`${apiBase}/graph/`, fetcher);

  const statCards = [
    { label: "Total Entities", value: graph?.nodes?.length?.toString() ?? "100" },
    { label: "Active Claims", value: graph?.edges?.length?.toString() ?? "30" },
    { label: "Current Regime", value: regime?.regime ?? "AI_CAPEX_EXPANSION" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-1">Bottleneck Dashboard</h1>
      <p className="text-slate-400 text-sm mb-6">
        Ranked transmission bottlenecks across the US AI infrastructure stack
      </p>

      <div className="grid grid-cols-3 gap-4 mb-8">
        {statCards.map(({ label, value }) => (
          <div key={label} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <p className="text-xs text-slate-400 mb-1">{label}</p>
            <p className="text-xl font-semibold text-white">{value}</p>
          </div>
        ))}
      </div>

      <BottleneckBoard limit={20} />
    </div>
  );
}
