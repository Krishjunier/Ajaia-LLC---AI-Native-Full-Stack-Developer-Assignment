import { useState, useEffect } from 'react'
import api from '../../api/axios'
import { useDocumentStore } from '../../store/documentStore'
import { useAuthStore } from '../../store/authStore'

function formatDate(dt) {
  const d = new Date(dt)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export default function Sidebar({ onNewDoc }) {
  const { documents, activeDocId, setDocuments, setActiveDocId } = useDocumentStore()
  const { user, logout } = useAuthStore()
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark')

  useEffect(() => {
    api.get('/documents').then((r) => setDocuments(r.data))
  }, [])

  useEffect(() => {
    if (theme === 'light') {
      document.documentElement.classList.add('light')
    } else {
      document.documentElement.classList.remove('light')
    }
    localStorage.setItem('theme', theme)
  }, [theme])

  const owned  = documents.filter((d) => d.role === 'owner')
  const shared = documents.filter((d) => d.role !== 'owner')

  const DocItem = ({ doc }) => (
    <div
      className={`sidebar-item ${doc.id === activeDocId ? 'active' : ''}`}
      onClick={() => setActiveDocId(doc.id)}
    >
      <span className="sidebar-item-icon">
        {doc.role === 'owner' ? '📄' : '👁'}
      </span>
      <div className="sidebar-item-content">
        <div className="sidebar-item-title">{doc.title}</div>
        <div className="sidebar-item-meta">
          <span className={`badge badge-${doc.role}`}>{doc.role}</span>
          {' '}{formatDate(doc.updated_at)}
        </div>
      </div>
    </div>
  )

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">📝</div>
          <div className="sidebar-logo-text">Ajaia Docs</div>
        </div>
        <button className="btn btn-primary sidebar-new-btn" onClick={onNewDoc}>
          + New Document
        </button>
      </div>

      <div className="sidebar-body">
        {owned.length > 0 && (
          <>
            <div className="sidebar-section-label">My Documents</div>
            {owned.map((d) => <DocItem key={d.id} doc={d} />)}
          </>
        )}

        {shared.length > 0 && (
          <>
            <div className="sidebar-section-label" style={{ marginTop: 12 }}>Shared with me</div>
            {shared.map((d) => <DocItem key={d.id} doc={d} />)}
          </>
        )}

        {documents.length === 0 && (
          <div style={{ padding: '20px 8px', fontSize: 13, color: 'var(--text-muted)', textAlign: 'center' }}>
            No documents yet.<br />Create one to get started!
          </div>
        )}
      </div>

      <div className="sidebar-footer">
        <div className="user-avatar">{user?.name?.[0] || '?'}</div>
        <div className="user-info">
          <div className="user-name">{user?.name}</div>
          <div className="user-email">{user?.email}</div>
        </div>
        <button
          className="btn-icon"
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
          style={{ fontSize: '15px' }}
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
        <button className="btn-icon" title="Sign out" onClick={logout}>↪</button>
      </div>
    </div>
  )
}
