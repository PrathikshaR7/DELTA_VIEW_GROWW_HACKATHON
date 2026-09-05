import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function Login() {
  const { doLogin } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await doLogin(email, password)
      navigate('/')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-950 px-4">
      <div className="w-full max-w-sm bg-surface-900 border border-teal-800/40 rounded-xl p-8 shadow-xl">
        <h1 className="text-xl font-semibold text-teal-50 mb-1">Smart Market Watchlist</h1>
        <p className="text-sm text-teal-400 mb-6">Sign in to your watchlist</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-teal-400 mb-1">Email</label>
            <input
              type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg bg-surface-800 border border-teal-800/50 px-3 py-2 text-sm text-teal-50 focus:outline-none focus:border-teal-600"
            />
          </div>
          <div>
            <label className="block text-xs text-teal-400 mb-1">Password</label>
            <input
              type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg bg-surface-800 border border-teal-800/50 px-3 py-2 text-sm text-teal-50 focus:outline-none focus:border-teal-600"
            />
          </div>
          {error && <p className="text-xs text-coral-400">{error}</p>}
          <button
            type="submit" disabled={loading}
            className="w-full rounded-lg bg-teal-700 hover:bg-teal-600 transition-colors text-white text-sm font-medium py-2 disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        <p className="text-xs text-teal-400/70 mt-4">
          No account? <Link to="/register" className="text-teal-300 underline">Create one</Link>
        </p>
      </div>
    </div>
  )
}
