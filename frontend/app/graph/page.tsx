// TODO: Integrate react-force-graph-2d — wire to GET /graph/ and render nodes/edges
export default function GraphPage() {
  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">Transmission Graph Explorer</h1>
          <p className="text-slate-400 text-sm">Force-directed view of AI infrastructure dependencies</p>
        </div>
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-indigo-900/40 border border-indigo-700/40 text-xs text-indigo-300">
          Regime: AI_CAPEX_EXPANSION
        </span>
      </div>

      <div className="flex-1 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-full border-2 border-indigo-500/40 border-t-indigo-400 animate-spin mx-auto" />
          <p className="text-slate-400 text-sm">Graph loading...</p>
          <p className="text-slate-600 text-xs">react-force-graph-2d integration — Day 2</p>
        </div>
      </div>
    </div>
  );
}
