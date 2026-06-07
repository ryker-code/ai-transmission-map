// TODO: Replace skeleton rows with real BottleneckBoard component wired to GET /bottlenecks/
export default function Home() {
  const statCards = [
    { label: "Total Entities", value: "--" },
    { label: "Active Claims", value: "--" },
    { label: "Current Regime", value: "AI_CAPEX_EXPANSION" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-1">Bottleneck Dashboard</h1>
      <p className="text-slate-400 text-sm mb-6">
        Ranked transmission bottlenecks across the US AI infrastructure stack
      </p>

      {/* Stat cards */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {statCards.map(({ label, value }) => (
          <div key={label} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <p className="text-xs text-slate-400 mb-1">{label}</p>
            <p className="text-xl font-semibold text-white">{value}</p>
          </div>
        ))}
      </div>

      {/* Skeleton bottleneck list */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-800">
          <span className="text-sm font-medium text-slate-300">Top Bottlenecks</span>
        </div>
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex items-center gap-4 px-4 py-3 border-b border-slate-800/50 last:border-0">
            <span className="w-6 text-xs text-slate-500 font-mono">{i}</span>
            <div className="flex-1 space-y-1.5">
              <div className="h-3 bg-slate-800 rounded animate-pulse w-48" />
              <div className="h-2 bg-slate-800/60 rounded animate-pulse w-32" />
            </div>
            <div className="h-5 w-12 bg-slate-800 rounded animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}
