import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({ baseURL: BASE_URL })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export function wsUrl() {
  const url = new URL(BASE_URL)
  const proto = url.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${url.host}/ws/quotes`
}

export async function login(email, password) {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  const { data } = await api.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

export async function register(email, password) {
  const { data } = await api.post('/auth/register', { email, password })
  return data
}

export const getWatchlist = () => api.get('/watchlist').then((r) => r.data)
export const addSymbol = (symbol) => api.post('/watchlist', { symbol }).then((r) => r.data)
export const removeSymbol = (id) => api.delete(`/watchlist/${id}`)
export const markSeen = () => api.post('/watchlist/mark-seen')
export const getQuotes = () => api.get('/market/quotes').then((r) => r.data)
export const searchSymbols = (q) => api.get('/market/search', { params: { q } }).then((r) => r.data)
export const getHistory = (symbol, hours = 6) =>
  api.get(`/market/history/${symbol}`, { params: { hours } }).then((r) => r.data)
