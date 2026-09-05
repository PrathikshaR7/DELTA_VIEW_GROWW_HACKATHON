import React from 'react'

function fmt(n, digits = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return '-'
  return Number(n).toLocaleString('en-IN', { maximumFractionDigits: digits, minimumFractionDigits: digits })
}

function scoreColor(score) {
  if (score === null || score === undefined) return 'bg-slate-800 text-slate-400 border border-slate-700'
  if (score >= 60) return 'bg-sky-500/20 text-sky-300 border border-sky-500/40'
  if (score >= 30) return 'bg-slate-800 text-sky-400 border border-slate-700'
  return 'bg-slate-800/60 text-slate-400 border border-slate-700/60'
}

export default function WatchlistTable({ rows, onSelect, onRemove }) {
  const columns = [
    'Symbol', 'Open', 'High', 'Low', 'Prev. Close', 'LTP', 'Change', '% Change',
    'Volume', 'Value (Cr)', '52W High', '52W Low', 'Since last visit', 'Score', '',
  ]

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800 bg-surface-900 shadow-xl">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-slate-800 bg-surface-950/60 text-slate-400 text-xs uppercase tracking-wider">
            {columns.map((c, i) => (
              <th key={c || i} className="px-4 py-3 text-left font-medium whitespace-nowrap">{c}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60 font-mono">
          {rows.map((r) => {
            const hasChange = r.change !== null && r.change !== undefined
            const isUp = hasChange && r.change >= 0
            const sinceLastUp = (r.since_last_seen_pct ?? 0) >= 0

            return (
              <tr
                key={r.symbol}
                onClick={() => onSelect(r)}
                className="hover:bg-slate-800/40 cursor-pointer transition-colors"
              >
                <td className="px-4 py-3.5 font-bold font-sans text-slate-100 whitespace-nowrap">{r.symbol}</td>
                <td className="px-4 py-3.5 text-slate-300">{fmt(r.open)}</td>
                <td className="px-4 py-3.5 text-slate-300">{fmt(r.high)}</td>
                <td className="px-4 py-3.5 text-slate-300">{fmt(r.low)}</td>
                <td className="px-4 py-3.5 text-slate-300">{fmt(r.prev_close)}</td>
                <td className="px-4 py-3.5 font-bold text-slate-100">{fmt(r.ltp)}</td>
                
                {/* Dedicated High-Contrast Green / Red Indicators */}
                <td className={`px-4 py-3.5 font-bold ${hasChange ? (isUp ? 'text-emerald-400' : 'text-rose-500') : 'text-slate-500'}`}>
                  {hasChange ? (isUp ? '+' : '') + fmt(r.change) : '-'}
                </td>
                <td className={`px-4 py-3.5 font-bold ${hasChange ? (isUp ? 'text-emerald-400' : 'text-rose-500') : 'text-slate-500'}`}>
                  {hasChange ? (isUp ? '+' : '') + fmt(r.pct_change) + '%' : '-'}
                </td>

                <td className="px-4 py-3.5 text-slate-300">{fmt(r.volume, 0)}</td>
                <td className="px-4 py-3.5 text-slate-300">{fmt(r.value_crores)}</td>
                <td className="px-4 py-3.5 text-slate-400">{fmt(r.week52_high)}</td>
                <td className="px-4 py-3.5 text-slate-400">{fmt(r.week52_low)}</td>
                
                <td className="px-4 py-3.5 whitespace-nowrap font-sans">
                  {r.is_new_since_last_visit ? (
                    <span className="text-xs text-sky-400 font-medium">new to you</span>
                  ) : r.since_last_seen_pct !== null && r.since_last_seen_pct !== undefined ? (
                    <span className={`font-mono ${sinceLastUp ? 'text-emerald-400' : 'text-rose-500'}`}>
                      {sinceLastUp ? '+' : ''}{fmt(r.since_last_seen_pct)}%
                    </span>
                  ) : (
                    <span className="text-xs text-slate-500">-</span>
                  )}
                </td>
                <td className="px-4 py-3.5 font-sans">
                  <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${scoreColor(r.mcs_score)}`}>
                    {r.mcs_score ?? '-'}
                  </span>
                </td>
                <td className="px-4 py-3.5 font-sans">
                  <button
                    onClick={(e) => { e.stopPropagation(); onRemove(r) }}
                    className="text-xs text-slate-400 hover:text-rose-400 transition-colors"
                  >
                    remove
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      {rows.length === 0 && (
        <p className="text-center text-sm text-slate-400 py-10 font-sans">
          Your watchlist is empty. Add a symbol to get started.
        </p>
      )}
    </div>
  )
}