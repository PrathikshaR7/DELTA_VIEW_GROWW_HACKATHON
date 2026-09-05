import { createContext, useContext, useState, useCallback } from 'react'
import * as api from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'))

  const doLogin = useCallback(async (email, password) => {
    const data = await api.login(email, password)
    localStorage.setItem('token', data.access_token)
    setToken(data.access_token)
  }, [])

  const doRegister = useCallback(async (email, password) => {
    await api.register(email, password)
    await doLogin(email, password)
  }, [doLogin])

  const doLogout = useCallback(() => {
    localStorage.removeItem('token')
    setToken(null)
  }, [])

  return (
    <AuthContext.Provider value={{ token, isAuthenticated: !!token, doLogin, doRegister, doLogout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
