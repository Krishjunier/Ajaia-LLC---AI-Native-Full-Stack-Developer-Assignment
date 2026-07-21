# Ajaia Docs — Collaborative Document Editor

A lightweight Google Docs–inspired collaborative document editor built as part of the Ajaia AI-Native Full Stack Developer assignment.

**Live demo:** _See SUBMISSION.md for deployment URL_

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite |
| Editor | Tiptap (ProseMirror-based, MIT) |
| State | Zustand |
| HTTP | Axios |
| Backend | FastAPI (Python 3.11+) |
| Database | SQLite via SQLAlchemy |
| Auth | Mock JWT (seeded users) |
| Testing | pytest |

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- pip

### 1 — Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The server will:
- Create `ajaia_docs.db` (SQLite) automatically
- Seed 3 demo users on first start
- Expose the API at `http://localhost:8000`
- Serve interactive API docs at `http://localhost:8000/docs`

### 2 — Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

### 3 — Run Tests

```bash
cd backend
pytest tests/ -v
```

---

## Demo Accounts

| Name | Email | Password |
|---|---|---|
| Alice | alice@ajaia.com | password123 |
| Bob | bob@ajaia.com | password123 |
| Carol | carol@ajaia.com | password123 |

### Reviewing the Sharing Flow

1. Log in as **Alice** → create a document → click **🔗 Share**
2. Grant **Bob** `viewer` access and **Carol** `editor` access
3. Log out → log in as **Bob** → see the document in "Shared with me" (read-only)
4. Log out → log in as **Carol** → same document is editable

---

## Features

### Document Editing
- Create, rename, delete documents
- Rich-text formatting: **Bold**, *Italic*, Underline, Strikethrough
- Headings H1–H3, Bullet lists, Numbered lists
- Text alignment (left, center, right)
- Blockquote, Inline code
- Undo / Redo
- Auto-save (3-second debounce) with status indicator

### File Upload
- Upload `.txt`, `.md`, or `.docx` files (max 5 MB)
- Converts to editable rich-text document
- Drag-and-drop interface

### Sharing
- Share with any other user as `viewer` (read-only) or `editor`
- Change permission in place, revoke access
- Visual distinction: owned docs show 🏷️ `owner`, shared docs show 👁️ role badge
- Viewer sees read-only banner; toolbar editing is disabled

### Persistence
- SQLite stores all documents and shares
- Content survives browser refresh
- Formatting is preserved as HTML

---

## API Reference

```
POST   /auth/login
GET    /users
GET    /documents
POST   /documents
GET    /documents/{id}
PUT    /documents/{id}
DELETE /documents/{id}
POST   /documents/{id}/upload
POST   /documents/{id}/share
DELETE /documents/{id}/share/{user_id}
GET    /documents/{id}/shares
GET    /health
```

Full interactive API docs: `http://localhost:8000/docs`

---

## File Upload Supported Types

| Type | Extension | Notes |
|---|---|---|
| Plain text | `.txt` | Each line becomes a paragraph |
| Markdown | `.md` | Full CommonMark parsing |
| Word document | `.docx` | Extracts headings + inline formatting |

Unsupported types return HTTP 400. Files over 5 MB return HTTP 413.

---

## Environment Variables

### Backend
| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `ajaia-super-secret-key-change-in-prod` | JWT signing key |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:4173` | CORS allowed origins |

### Frontend
| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Backend API base URL |

---

## What Is Intentionally Not Included

- **Real-time multi-cursor collaboration** — WebSocket + CRDT complexity doesn't fit the timebox; auto-save every 3s provides a sensible alternative
- **PDF export** — not a core requirement
- **Version history** — architectural decision to ship core flows well
- **Production auth** — mocked JWT with seeded users keeps reviewer setup friction near zero
- **Email notifications** — no email infrastructure in scope

---

## What Would Come Next (with another 2–4 hours)

1. WebSocket real-time collaboration (Tiptap collaboration extension + Y.js)
2. Document version history with diff viewer
3. Commenting / suggestion mode
4. Export to PDF / Markdown
5. Full OAuth2 (Google login)
