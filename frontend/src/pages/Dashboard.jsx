import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { getWatchlist, getQuotes, addSymbol, removeSymbol, markSeen, wsUrl } from '../api'
import WatchlistTable from '../components/WatchlistTable.jsx'
import StockDetailModal from '../components/StockDetailModal.jsx'
import AddSymbolModal from '../components/AddSymbolModal.jsx'

export default function Dashboard() {
  const { doLogout } = useAuth()
  const [quotes, setQuotes] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [showAdd, setShowAdd] = useState(false)
  const wsRef = useRef(null)

  const refresh = useCallback(async () => {
    const watchlist = await getWatchlist()
    if (watchlist.length === 0) {
      setQuotes([])
      setLoading(false)
      return
    }
    const data = await getQuotes()
    setQuotes(data)
    setLoading(false)
    // Snapshot "last seen" a moment after rendering the diff, so this
    // visit's diff (computed against the PREVIOUS visit) has already been
    // shown to the user before we roll the baseline forward.
    setTimeout(() => { markSeen().catch(() => {}) }, 4000)
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  // live updates over websocket - merge into whichever rows are tracked
  useEffect(() => {
    const ws = new WebSocket(wsUrl())
    wsRef.current = ws
    ws.onmessage = (event) => {
      try {
        const update = JSON.parse(event.data)
        setQuotes((prev) => {
          const idx = prev.findIndex((q) => q.symbol === update.symbol)
          if (idx === -1) return prev // not on this user's list
          const next = [...prev]
          next[idx] = { ...next[idx], ...update }
          return next
        })
      } catch {
        // ignore malformed frames
      }
    }
    return () => ws.close()
  }, [])

  async function handleAdd(symbol) {
    await addSymbol(symbol)
    await refresh()
  }

  async function handleRemove(row) {
    const watchlist = await getWatchlist()
    const item = watchlist.find((w) => w.symbol === row.symbol)
    if (item) await removeSymbol(item.id)
    await refresh()
  }

  const topMovers = [...quotes]
    .filter((q) => q.mcs_score !== null && q.mcs_score !== undefined)
    .sort((a, b) => b.mcs_score - a.mcs_score)
    .slice(0, 3)

  const dataMode = quotes[0]?.data_mode

  return (
    <div className="min-h-screen bg-surface-950 text-teal-50 px-4 sm:px-8 py-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-3">
              <svg
                aria-hidden="true"
                className="h-9 w-9 text-teal-400"
                viewBox="0 0 40 40"
                fill="none"
              >
                <path d="M7 31 19.5 7 33 31H7Z" stroke="currentColor" strokeWidth="3" strokeLinejoin="round" />
                <path d="m13 26 6-7 4 4 7-9" stroke="#72E6B3" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <h1 className="text-3xl font-bold tracking-wide">DELTA VIEW</h1>
            </div>
            <h2 className="text-xl font-semibold text-teal-500 mt-1">Your Smart Market Watchlist</h2>
            <p className="text-sm text-teal-500">
              {dataMode === 'replay'
                ? 'Market closed - showing a real historical session on replay'
                : 'Live market data'}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowAdd(true)}
              className="px-3 py-2 rounded-lg bg-teal-700 hover:bg-teal-600 text-sm font-medium"
            >
              + Add symbol
            </button>
            <button onClick={doLogout} className="text-sm text-teal-500 hover:text-teal-200">
              Logout
            </button>
          </div>
        </div>

        {topMovers.length > 0 && (
          <div className="mb-6 p-4 rounded-xl bg-surface-900 border border-teal-800/40">
            <p className="text-xs uppercase tracking-wide text-teal-500 mb-2">Deserves your attention today</p>
            <div className="space-y-1">
              {topMovers.map((m) => (
                <p key={m.symbol} className="text-sm text-teal-200">
                  <span className="font-semibold text-teal-50">{m.symbol}</span> - {m.mcs_reason}
                </p>
              ))}
            </div>
          </div>
        )}

        {loading ? (
          <p className="text-teal-500 text-sm">Loading your watchlist...</p>
        ) : (
          <WatchlistTable rows={quotes} onSelect={setSelected} onRemove={handleRemove} />
        )}
      </div>

      {selected && <StockDetailModal stock={selected} onClose={() => setSelected(null)} />}
      {showAdd && <AddSymbolModal onClose={() => setShowAdd(false)} onAdd={handleAdd} />}
    </div>
  )
}
