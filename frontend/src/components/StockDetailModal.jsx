import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { getHistory } from '../api'

const COMPONENT_LABELS = {
  mcs_z_score: 'Move vs its usual volatility',
  mcs_volume_ratio: 'Volume vs its average',
  mcs_near_52w: 'Proximity to 52-week high/low',
  mcs_vs_index: 'Divergence from Nifty 50',
}

function fmt(n, digits = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return '-'
  return Number(n).toLocaleString('en-IN', { maximumFractionDigits: digits, minimumFractionDigits: digits })
}

// Data points arrive one per ingestion cycle (as little as 15s apart). A
// plain "hour:minute" label collapses several distinct points onto the same
// tick text (e.g. "01:01 pm" three times in a row), which is what made the
// chart look broken/duplicated. Once the visible history spans less than an
// hour, switch to hour:minute:second so every tick is unique; for longer
// spans, minute-level labels are still readable and stay uncluttered.
function formatTick(ts, spanMs) {
  const showSeconds = spanMs < 60 * 60 * 1000
  return new Date(ts).toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    ...(showSeconds ? { second: '2-digit' } : {}),
  })
}

export default function StockDetailModal({ stock, onClose }) {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  const isPositive = (stock.pct_change ?? 0) >= 0

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getHistory(stock.symbol, 6)
      .then((data) => {
        if (cancelled) return
        const spanMs = data.length > 1
          ? new Date(data[data.length - 1].ts) - new Date(data[0].ts)
          : 0
        setHistory(
          data.map((d) => ({
            time: formatTick(d.ts, spanMs),
            ltp: d.ltp,
          }))
        )
      })
      .finally(() => !cancelled && setLoading(false))
    return () => { cancelled = true }
  }, [stock.symbol])

  const components = [
    { key: 'mcs_z_score', value: stock.mcs_z_score },
    { key: 'mcs_volume_ratio', value: stock.mcs_volume_ratio },
    { key: 'mcs_near_52w', value: stock.mcs_near_52w },
    { key: 'mcs_vs_index', value: stock.mcs_vs_index },
  ]

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm px-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-surface-900 border border-teal-800/60 rounded-xl p-6 shadow-2xl max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-100">{stock.symbol}</h2>
            <div className="flex items-center gap-2 text-sm mt-0.5">
              <span className="text-slate-300 font-medium">LTP {fmt(stock.ltp)}</span>
              <span className="text-slate-500">·</span>
              <span className={`font-semibold ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
                {isPositive ? '+' : ''}{fmt(stock.pct_change)}%
              </span>
              {stock.data_mode === 'replay' && (
                <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-slate-800 text-teal-200 border border-slate-700">
                  Market closed · replaying real session {stock.source_session_date}
                </span>
              )}
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200 text-sm font-medium transition-colors">
            close
          </button>
        </div>

        <div className="mb-5 p-4 rounded-lg bg-surface-800/50 border border-slate-700/60">
          <p className="text-xs uppercase tracking-wider text-teal-400 font-medium mb-1">Meaningful Change Score</p>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl font-bold text-slate-50">{stock.mcs_score ?? '-'}</span>
            <span className="text-xs text-slate-400">/ 100</span>
          </div>
          <p className="text-sm text-slate-300">{stock.mcs_reason}</p>
        </div>

        <div className="mb-5 space-y-2.5">
          <p className="text-xs uppercase tracking-wider text-teal-400 font-medium">Score breakdown</p>
          {components.map((c) => (
            <div key={c.key} className="flex items-center gap-3">
              <span className="text-xs text-slate-300 w-56 shrink-0">{COMPONENT_LABELS[c.key]}</span>
              <div className="flex-1 h-2 rounded-full bg-surface-800 overflow-hidden border border-slate-700/50">
                <div
                  className="h-full bg-teal-400 rounded-full"
                  style={{ width: `${Math.round((c.value ?? 0) * 100)}%` }}
                />
              </div>
              <span className="text-xs text-slate-300 font-mono w-10 text-right">{Math.round((c.value ?? 0) * 100)}%</span>
            </div>
          ))}
        </div>

        <div>
          <p className="text-xs uppercase tracking-wider text-teal-400 font-medium mb-2">Price path (today's session)</p>
          <div className="h-56">
            {loading ? (
              <p className="text-sm text-slate-400">Loading chart...</p>
            ) : history.length === 0 ? (
              <p className="text-sm text-slate-400">No history yet - check back after the worker has run a few cycles.</p>
            ) : history.length < 4 ? (
              <p className="text-sm text-slate-400">
                Only {history.length} data point{history.length === 1 ? '' : 's'} so far - this symbol was added
                recently. The chart fills in as the ingestion worker keeps polling (every few seconds); check back shortly.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#273b61" opacity={0.4} />
                  <XAxis
                    dataKey="time"
                    stroke="#94a3b8"
                    fontSize={11}
                    tickLine={false}
                    minTickGap={24}
                  />
                  <YAxis stroke="#94a3b8" fontSize={11} domain={['auto', 'auto']} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: '#0f172a', border: '1px solid #273b61', borderRadius: 8 }}
                    labelStyle={{ color: '#bae6fd' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="ltp"
                    stroke={isPositive ? '#15de5fff' : '#f62c2cff'}
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
