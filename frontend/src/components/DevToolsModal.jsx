import React, { useState, useEffect } from 'react';

export default function DevToolsModal({ isOpen, onClose }) {
  const [leaderboard, setLeaderboard] = useState(null);
  const [scorecard, setScorecard] = useState(null);
  const [registry, setRegistry] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetch("http://127.0.0.1:8000/arena/leaderboard")
        .then(r => r.json())
        .then(d => setLeaderboard(d))
        .catch(() => {});

      fetch("http://127.0.0.1:8000/arena/scorecard")
        .then(r => r.json())
        .then(d => setScorecard(d))
        .catch(() => {});

      fetch("http://127.0.0.1:8000/models/registry")
        .then(r => r.json())
        .then(d => setRegistry(d))
        .catch(() => {});
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-4xl max-h-[85vh] overflow-y-auto p-6 shadow-2xl border border-slate-200 dark:border-slate-800 space-y-6">
        <div className="flex justify-between items-center pb-4 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              🛠️ Developer Tools & Model Arena Internals
            </h2>
            <p className="text-xs text-slate-500">
              Rule P-R1: Internal model architectures, metrics, and scorecards are isolated from user-facing screens.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xl font-bold"
          >
            &times;
          </button>
        </div>

        {/* Champion & Registry Status */}
        <div className="bg-slate-50 dark:bg-slate-800/60 p-4 rounded-xl border border-slate-200 dark:border-slate-700 text-xs space-y-2">
          <div className="flex justify-between font-mono">
            <span>Delay Champion: <strong className="text-emerald-600 dark:text-emerald-400">{registry?.delay?.champion || "m3_xgboost"}</strong></span>
            <span>Crowd Champion: <strong className="text-emerald-600 dark:text-emerald-400">{registry?.crowding?.champion || "m3_xgboost"}</strong></span>
            <span>Approved by Human: <strong className={registry?.approved_by_human ? "text-emerald-500" : "text-amber-500"}>{String(registry?.approved_by_human)}</strong></span>
          </div>
        </div>

        {/* Model Arena Leaderboard Table */}
        <div>
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-2">Frozen Harness Leaderboard</h3>
          <div className="overflow-x-auto border border-slate-200 dark:border-slate-800 rounded-xl">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-semibold">
                <tr>
                  <th className="py-2.5 px-3">Model ID</th>
                  <th className="py-2.5 px-3">Family</th>
                  <th className="py-2.5 px-3">Delay MAE</th>
                  <th className="py-2.5 px-3">80% Cov</th>
                  <th className="py-2.5 px-3">Crowd QWK</th>
                  <th className="py-2.5 px-3">Latency (p50)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono">
                {leaderboard?.models ? Object.entries(leaderboard.models).map(([mid, m]) => (
                  <tr key={mid} className={mid === 'm3_xgboost' ? 'bg-emerald-50/50 dark:bg-emerald-950/20 font-bold' : ''}>
                    <td className="py-2 px-3 font-sans">{mid === 'm3_xgboost' ? '🏆 ' : ''}{mid}</td>
                    <td className="py-2 px-3 font-sans text-slate-500">{m.family}</td>
                    <td className="py-2 px-3">{m.delay?.mae}m</td>
                    <td className="py-2 px-3">{m.delay?.interval_coverage ? `${(m.delay.interval_coverage * 100).toFixed(1)}%` : 'N/A'}</td>
                    <td className="py-2 px-3">{m.crowding?.qwk ?? 'N/A'}</td>
                    <td className="py-2 px-3">{m.operational?.latency_ms_p50}ms</td>
                  </tr>
                )) : (
                  <tr><td colSpan="6" className="py-3 px-3 text-center text-slate-400">Loading arena metrics...</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Significance Tests */}
        {leaderboard?.significance && (
          <div className="bg-slate-50 dark:bg-slate-800/40 p-4 rounded-xl border border-slate-200 dark:border-slate-800 text-xs">
            <h4 className="font-bold text-slate-700 dark:text-slate-300 mb-2">Paired Bootstrap Significance Tests (1000 Resamples, 95% CI)</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-slate-600 dark:text-slate-400 font-mono text-[11px]">
              <div>
                • GNN vs GRU Difference: {leaderboard.significance.gnn_vs_gru?.mean_diff}m (CI: [{leaderboard.significance.gnn_vs_gru?.ci_95?.[0]}m, {leaderboard.significance.gnn_vs_gru?.ci_95?.[1]}m])
              </div>
              <div>
                • GNN Graph vs No-Graph: {leaderboard.significance.gnn_graph_vs_nograph?.mean_diff}m (Significant: {String(leaderboard.significance.gnn_graph_vs_nograph?.significant)})
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

