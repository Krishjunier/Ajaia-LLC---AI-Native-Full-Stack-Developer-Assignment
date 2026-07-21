import { useState, useRef } from 'react'
import api from '../../api/axios'

const ACCEPTED = '.txt,.md,.docx'

export default function UploadModal({ doc, onClose, onSuccess }) {
  const [file, setFile]       = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress]  = useState(0)
  const [error, setError]        = useState('')
  const inputRef = useRef()

  const handleFile = (f) => {
    setError('')
    setFile(f)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  const handleUpload = async () => {
    if (!file) return
    setError('')
    setUploading(true)
    setProgress(10)
    try {
      const form = new FormData()
      form.append('file', file)
      setProgress(40)
      const res = await api.post(`/documents/${doc.id}/upload`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setProgress(100)
      setTimeout(() => {
        onSuccess(res.data)
        onClose()
      }, 300)
    } catch (e) {
      setError(e.response?.data?.detail || 'Upload failed. Please try again.')
      setProgress(0)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title">📁 Import File</div>
          <button className="btn-icon" onClick={onClose}>✕</button>
        </div>

        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
          Import a file into <strong style={{ color: 'var(--text-primary)' }}>{doc.title}</strong>.
          Its content will replace the current document content.
        </p>

        <div
          className={`upload-dropzone ${dragOver ? 'drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED}
            style={{ display: 'none' }}
            onChange={(e) => handleFile(e.target.files[0])}
          />
          <div className="upload-icon">⬆️</div>
          <div className="upload-text">Drag & drop or click to browse</div>
          <div className="upload-hint">Supported: .txt, .md, .docx · Max 5 MB</div>
        </div>

        {file && (
          <div className="upload-file-name">
            📄 {file.name}
            <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-muted)' }}>
              {(file.size / 1024).toFixed(1)} KB
            </span>
          </div>
        )}

        {progress > 0 && progress < 100 && (
          <div className="upload-progress">
            <div className="upload-progress-bar" style={{ width: `${progress}%` }} />
          </div>
        )}

        {error && (
          <div className="login-error" style={{ marginTop: 12 }}>{error}</div>
        )}

        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose} disabled={uploading}>Cancel</button>
          <button
            className="btn btn-primary"
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            {uploading ? <><span className="spinner" /> Importing…</> : '⬆ Import'}
          </button>
        </div>
      </div>
    </div>
  )
}
