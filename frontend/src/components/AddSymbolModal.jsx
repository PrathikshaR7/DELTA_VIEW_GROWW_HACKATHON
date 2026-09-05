import { useEffect, useState } from 'react'
import { searchSymbols } from '../api'

export default function AddSymbolModal({ onClose, onAdd }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [adding, setAdding] = useState(null)

  useEffect(() => {
    let cancelled = false
    searchSymbols(query).then((data) => !cancelled && setResults(data))
    return () => { cancelled = true }
  }, [query])

  async function handleAdd(symbol) {
    setAdding(symbol)
    try {
      await onAdd(symbol)
      onClose()
    } finally {
      setAdding(null)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4" onClick={onClose}>
      <div
        className="w-full max-w-md bg-surface-900 border border-teal-800/50 rounded-xl p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-teal-50">Add to watchlist</h2>
          <button onClick={onClose} className="text-teal-500 hover:text-teal-200 text-sm">close</button>
        </div>
        <input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search symbol or company name"
          className="w-full rounded-lg bg-surface-800 border border-teal-800/50 px-3 py-2 text-sm text-teal-50 focus:outline-none focus:border-teal-600 mb-4"
        />
        <div className="space-y-1 max-h-72 overflow-y-auto">
          {results.map((r) => (
            <button
              key={r.symbol}
              onClick={() => handleAdd(r.symbol)}
              disabled={adding === r.symbol}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-surface-800 text-left disabled:opacity-50"
            >
              <span>
                <span className="text-teal-50 font-medium">{r.symbol}</span>
                <span className="text-teal-500 text-xs ml-2">{r.name}</span>
              </span>
              <span className="text-xs text-teal-400">{adding === r.symbol ? 'adding...' : 'add'}</span>
            </button>
          ))}
          {results.length === 0 && (
            <p className="text-sm text-teal-500 px-3 py-2">No matches</p>
          )}
        </div>
      </div>
    </div>
  )
}
