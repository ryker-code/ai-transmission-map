import BottleneckBoard from "@/components/BottleneckBoard";

const statCards = [
  { label: "Total Entities", value: "100" },
  { label: "Active Claims", value: "30" },
  { label: "Current Regime", value: "AI_CAPEX_EXPANSION" },
];

export default function Home() {
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
