import { useState } from 'react'
import api from '../api/axios'
import { useAuthStore } from '../store/authStore'

const DEMO_USERS = [
  { name: 'Alice', email: 'alice@ajaia.com', color: '#6c63ff' },
  { name: 'Bob',   email: 'bob@ajaia.com',   color: '#26c6da' },
  { name: 'Carol', email: 'carol@ajaia.com', color: '#f06292' },
]

export default function LoginPage() {
  const [isSignup, setIsSignup] = useState(false)
  const [name, setName]         = useState('')
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
      if (isSignup) {
        const res = await api.post('/auth/signup', { name, email, password })
        login(res.data.user, res.data.access_token)
      } else {
        const res = await api.post('/auth/login', { email, password })
        login(res.data.user, res.data.access_token)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Please try again.')
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
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="auth-logo-icon">📝</div>
          <h1 className="auth-logo-title">Ajaia Docs</h1>
          <div className="auth-logo-sub">Collaborative document editor</div>
        </div>

        {/* Tab Switcher */}
        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab ${!isSignup ? 'active' : ''}`}
            onClick={() => { setIsSignup(false); setError(''); }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`auth-tab ${isSignup ? 'active' : ''}`}
            onClick={() => { setIsSignup(true); setError(''); }}
          >
            Sign Up
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <div className="auth-error">{error}</div>}

          {isSignup && (
            <div className="form-group">
              <label className="form-label">Name</label>
              <input
                className="input"
                type="text"
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                autoFocus
              />
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              className="input"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus={!isSignup}
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

          <button className="btn btn-primary auth-submit" type="submit" disabled={loading}>
            {loading ? (
              <>
                <span className="spinner"></span> {isSignup ? 'Creating account…' : 'Signing in…'}
              </>
            ) : (
              isSignup ? 'Create account' : 'Sign in'
            )}
          </button>
        </form>

        {!isSignup && (
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
        )}
      </div>
    </div>
  )
}

