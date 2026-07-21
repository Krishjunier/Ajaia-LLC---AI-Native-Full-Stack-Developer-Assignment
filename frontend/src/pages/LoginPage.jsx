import { useState } from 'react'
import api from '../api/axios'
import { useAuthStore } from '../store/authStore'

const DEMO_USERS = [
  { name: 'Alice', email: 'alice@ajaia.com', color: '#6c63ff' },
  { name: 'Bob',   email: 'bob@ajaia.com',   color: '#26c6da' },
  { name: 'Carol', email: 'carol@ajaia.com', color: '#f06292' },
]

export default function LoginPage() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const login = useAuthStore((s) => s.login)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api.post('/auth/login', { email, password })
      login(res.data.user, res.data.access_token)
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const fillDemo = (u) => {
    setEmail(u.email)
    setPassword('password123')
    setError('')
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <div className="login-logo-icon">📝</div>
          <div className="login-logo-title">Ajaia Docs</div>
          <div className="login-logo-sub">Collaborative document editor</div>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {error && <div className="login-error">{error}</div>}

          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              className="input"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className="input"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button className="btn btn-primary" type="submit" disabled={loading} style={{ marginTop: 4 }}>
            {loading ? <><span className="spinner"></span> Signing in…</> : 'Sign in'}
          </button>
        </form>

        <div className="demo-accounts">
          <div className="demo-accounts-title">🔑 Demo Accounts (click to fill)</div>
          {DEMO_USERS.map((u) => (
            <button key={u.email} className="demo-account-btn" type="button" onClick={() => fillDemo(u)}>
              <div className="demo-avatar" style={{ background: u.color }}>{u.name[0]}</div>
              <div className="demo-user-info">
                <div className="demo-name">{u.name}</div>
                <div className="demo-email">{u.email} · password123</div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
