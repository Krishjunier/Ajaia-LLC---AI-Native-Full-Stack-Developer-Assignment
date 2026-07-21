import { useState, useEffect, useRef, useCallback } from 'react'
import api from '../api/axios'
import { useDocumentStore } from '../store/documentStore'
import { useAuthStore } from '../store/authStore'
import Sidebar from '../components/Sidebar/Sidebar'
import RichEditor from '../components/Editor/RichEditor'
import ShareModal from '../components/ShareModal/ShareModal'
import UploadModal from '../components/UploadModal/UploadModal'

const AUTOSAVE_DELAY = 3000 // 3 seconds debounce

export default function EditorPage() {
  const { documents, activeDocId, setDocuments, addDocument, updateDocument, removeDocument } =
    useDocumentStore()
  const user = useAuthStore((s) => s.user)

  const [activeDoc, setActiveDoc]     = useState(null)
  const [title, setTitle]             = useState('')
  const [content, setContent]         = useState('')
  const [saveStatus, setSaveStatus]   = useState('saved') // 'saved' | 'saving' | 'error'
  const [showShare, setShowShare]     = useState(false)
  const [showUpload, setShowUpload]   = useState(false)
  const [showExport, setShowExport]   = useState(false)
  const [deleting, setDeleting]       = useState(false)

  const saveTimer = useRef(null)
  const editorRef = useRef(null)
  const exportRef = useRef(null)

  // Click outside export dropdown handler
  useEffect(() => {
    function handleClickOutside(event) {
      if (exportRef.current && !exportRef.current.contains(event.target)) {
        setShowExport(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Export document handler
  const handleExport = async (format) => {

    try {
      const res = await api.get(`/documents/${activeDocId}/export`, {
        params: { format },
        responseType: 'blob',
      })
      const blob = new Blob([res.data], { type: res.headers['content-type'] })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      
      const disposition = res.headers['content-disposition']
      let filename = `${title || 'document'}.${format}`
      if (disposition && disposition.indexOf('filename=') !== -1) {
        const matches = /filename="([^"]+)"/.exec(disposition)
        if (matches != null && matches[1]) filename = matches[1]
      }
      
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      alert('Failed to export document. Please try again.')
    }
  }

  // Load active document
  useEffect(() => {
    if (!activeDocId) { setActiveDoc(null); return }
    api.get(`/documents/${activeDocId}`).then((r) => {
      setActiveDoc(r.data)
      setTitle(r.data.title)
      setContent(r.data.content)
    })
  }, [activeDocId])

  // ── Autosave ──────────────────────────────────────────────────────────────

  const save = useCallback(async (newContent) => {
    if (!activeDocId) return
    setSaveStatus('saving')
    try {
      const res = await api.put(`/documents/${activeDocId}`, { content: newContent })
      updateDocument({ id: res.data.id, title: res.data.title, updated_at: res.data.updated_at })
      setSaveStatus('saved')
    } catch {
      setSaveStatus('error')
    }
  }, [activeDocId])

  const handleContentChange = useCallback((html) => {
    setContent(html)
    setSaveStatus('saving')
    clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(() => save(html), AUTOSAVE_DELAY)
  }, [save])

  // ── Title rename ──────────────────────────────────────────────────────────

  const handleTitleBlur = async () => {
    if (!activeDoc || title === activeDoc.title) return
    if (!title.trim()) { setTitle(activeDoc.title); return }
    try {
      const res = await api.put(`/documents/${activeDocId}`, { title: title.trim() })
      updateDocument({ id: res.data.id, title: res.data.title })
      setActiveDoc((d) => ({ ...d, title: res.data.title }))
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to rename')
      setTitle(activeDoc.title)
    }
  }

  // ── Create document ───────────────────────────────────────────────────────

  const handleNewDoc = async () => {
    const res = await api.post('/documents', { title: 'Untitled Document', content: '' })
    addDocument({ ...res.data, role: 'owner' })
    useDocumentStore.getState().setActiveDocId(res.data.id)
  }

  // ── Delete document ───────────────────────────────────────────────────────

  const handleDelete = async () => {
    if (!activeDoc || !window.confirm(`Delete "${activeDoc.title}"? This cannot be undone.`)) return
    setDeleting(true)
    try {
      await api.delete(`/documents/${activeDocId}`)
      removeDocument(activeDocId)
      setActiveDoc(null)
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to delete')
    } finally {
      setDeleting(false)
    }
  }

  // ── Upload success handler ────────────────────────────────────────────────

  const handleUploadSuccess = (updatedDoc) => {
    setContent(updatedDoc.content)
    setActiveDoc(updatedDoc)
    if (editorRef.current) editorRef.current.setContent(updatedDoc.content)
    setSaveStatus('saved')
  }

  const isOwner   = activeDoc?.role === 'owner'
  const isViewer  = activeDoc?.role === 'viewer'
  const canEdit   = activeDoc?.role === 'owner' || activeDoc?.role === 'editor'

  const SaveIndicator = () => {
    const icons = { saved: '✓', saving: '…', error: '⚠' }
    const labels = { saved: 'Saved', saving: 'Saving…', error: 'Save failed — retrying' }
    return (
      <span className={`save-status ${saveStatus}`}>
        {icons[saveStatus]} {labels[saveStatus]}
      </span>
    )
  }

  return (
    <div className="app-layout">
      <Sidebar onNewDoc={handleNewDoc} />

      <div className="editor-area">
        {activeDoc ? (
          <>
            {/* Topbar */}
            <div className="editor-topbar">
              <input
                className="doc-title-input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                onBlur={handleTitleBlur}
                onKeyDown={(e) => e.key === 'Enter' && e.target.blur()}
                disabled={!isOwner}
                placeholder="Document title"
              />

              {activeDoc && <SaveIndicator />}

              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                {/* Role badge */}
                <span className={`badge badge-${activeDoc.role}`}>{activeDoc.role}</span>

                {/* Upload */}
                {canEdit && (
                  <button className="btn btn-ghost" onClick={() => setShowUpload(true)} title="Import file">
                    📁 Import
                  </button>
                )}

                {/* Export Dropdown */}
                <div ref={exportRef} className="export-dropdown-container" style={{ position: 'relative' }}>
                  <button className="btn btn-ghost" onClick={() => setShowExport(!showExport)} title="Export document">
                    📥 Export
                  </button>
                  {showExport && (
                    <div className="export-dropdown-menu">
                      <button className="export-dropdown-item" onClick={() => { handleExport('pdf'); setShowExport(false); }}>
                        📄 PDF (.pdf)
                      </button>
                      <button className="export-dropdown-item" onClick={() => { handleExport('md'); setShowExport(false); }}>
                        📝 Markdown (.md)
                      </button>
                      <button className="export-dropdown-item" onClick={() => { handleExport('html'); setShowExport(false); }}>
                        🌐 HTML (.html)
                      </button>
                      <button className="export-dropdown-item" onClick={() => { handleExport('txt'); setShowExport(false); }}>
                        🔤 Plain Text (.txt)
                      </button>
                    </div>
                  )}
                </div>

                {/* Share */}
                {isOwner && (
                  <button className="btn btn-ghost" onClick={() => setShowShare(true)}>
                    🔗 Share
                  </button>
                )}

                {/* Delete */}
                {isOwner && (
                  <button
                    className="btn btn-danger"
                    onClick={handleDelete}
                    disabled={deleting}
                    title="Delete document"
                  >
                    {deleting ? <span className="spinner" /> : '🗑'}
                  </button>
                )}
              </div>
            </div>

            {/* Viewer warning banner */}
            {isViewer && (
              <div style={{
                background: 'rgba(38,198,218,.08)',
                borderBottom: '1px solid rgba(38,198,218,.2)',
                padding: '8px 20px',
                fontSize: 12,
                color: 'var(--shared-color)',
              }}>
                👁 You have <strong>view-only</strong> access to this document. Editing is disabled.
              </div>
            )}

            {/* Editor */}
            <RichEditor
              ref={editorRef}
              content={content}
              onChange={handleContentChange}
              readOnly={isViewer}
            />
          </>
        ) : (
          <div className="empty-state">
            <div className="empty-state-icon">📝</div>
            <div className="empty-state-title">No document selected</div>
            <div className="empty-state-sub">Choose a document from the sidebar or create a new one</div>
            <button className="btn btn-primary" style={{ marginTop: 8 }} onClick={handleNewDoc}>
              + New Document
            </button>
          </div>
        )}
      </div>

      {showShare && activeDoc && (
        <ShareModal doc={activeDoc} onClose={() => setShowShare(false)} />
      )}

      {showUpload && activeDoc && (
        <UploadModal
          doc={activeDoc}
          onClose={() => setShowUpload(false)}
          onSuccess={handleUploadSuccess}
        />
      )}
    </div>
  )
}
