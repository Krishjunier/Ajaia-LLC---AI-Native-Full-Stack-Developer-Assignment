import { useState, useEffect } from 'react'
import api from '../../api/axios'
import { useDocumentStore } from '../../store/documentStore'

export default function ShareModal({ doc, onClose }) {
  const [users, setUsers]     = useState([])
  const [shares, setShares]   = useState([])
  const [addUserId, setAddUserId] = useState('')
  const [permission, setPermission] = useState('viewer')
  const [loading, setLoading] = useState(false)
  const updateDocument = useDocumentStore((s) => s.updateDocument)

  useEffect(() => {
    api.get('/users').then((r) => setUsers(r.data))
    api.get(`/documents/${doc.id}/shares`).then((r) => setShares(r.data))
  }, [doc.id])

  const sharedUserIds = new Set(shares.map((s) => s.user.id))
  const available = users.filter((u) => !sharedUserIds.has(u.id))

  const handleAdd = async () => {
    if (!addUserId) return
    setLoading(true)
    try {
      await api.post(`/documents/${doc.id}/share`, {
        user_id: parseInt(addUserId),
        permission,
      })
      const r = await api.get(`/documents/${doc.id}/shares`)
      setShares(r.data)
      setAddUserId('')
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to share')
    } finally {
      setLoading(false)
    }
  }

  const handleRevoke = async (userId) => {
    try {
      await api.delete(`/documents/${doc.id}/share/${userId}`)
      setShares((s) => s.filter((sh) => sh.user.id !== userId))
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to revoke')
    }
  }

  const handleChangePermission = async (userId, newPerm) => {
    try {
      await api.post(`/documents/${doc.id}/share`, {
        user_id: userId,
        permission: newPerm,
      })
      setShares((s) => s.map((sh) => sh.user.id === userId ? { ...sh, permission: newPerm } : sh))
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to update permission')
    }
  }

  return (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title">🔗 Share Document</div>
          <button className="btn-icon" onClick={onClose}>✕</button>
        </div>

        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4 }}>
          <strong style={{ color: 'var(--text-primary)' }}>{doc.title}</strong>
        </div>

        {/* Permission matrix info */}
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 16, lineHeight: 1.6 }}>
          <span className="badge badge-editor" style={{ marginRight: 6 }}>editor</span> can read &amp; edit &nbsp;·&nbsp;
          <span className="badge badge-viewer" style={{ marginRight: 6 }}>viewer</span> read only
        </div>

        {/* Current shares */}
        {shares.length > 0 && (
          <div className="share-list">
            {shares.map((sh) => (
              <div key={sh.user.id} className="share-item">
                <div className="user-avatar" style={{ width: 28, height: 28, fontSize: 11 }}>
                  {sh.user.name[0]}
                </div>
                <div className="share-item-info">
                  <div className="share-item-name">{sh.user.name}</div>
                  <div className="share-item-email">{sh.user.email}</div>
                </div>
                <select
                  className="share-permission-select"
                  value={sh.permission}
                  onChange={(e) => handleChangePermission(sh.user.id, e.target.value)}
                >
                  <option value="viewer">viewer</option>
                  <option value="editor">editor</option>
                </select>
                <button className="btn-icon" title="Revoke access" onClick={() => handleRevoke(sh.user.id)}>
                  🗑
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Add new share */}
        {available.length > 0 && (
          <div className="share-add-row">
            <select
              className="input"
              style={{ flex: 1 }}
              value={addUserId}
              onChange={(e) => setAddUserId(e.target.value)}
            >
              <option value="">Select a person…</option>
              {available.map((u) => (
                <option key={u.id} value={u.id}>{u.name} ({u.email})</option>
              ))}
            </select>
            <select
              className="share-permission-select"
              value={permission}
              onChange={(e) => setPermission(e.target.value)}
            >
              <option value="viewer">viewer</option>
              <option value="editor">editor</option>
            </select>
            <button className="btn btn-primary" onClick={handleAdd} disabled={!addUserId || loading}>
              {loading ? <span className="spinner" /> : 'Share'}
            </button>
          </div>
        )}

        {available.length === 0 && shares.length === 0 && (
          <p style={{ fontSize: 13, color: 'var(--text-muted)', textAlign: 'center', padding: '20px 0' }}>
            No other users to share with
          </p>
        )}

        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Done</button>
        </div>
      </div>
    </div>
  )
}
