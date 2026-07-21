# Architecture Note

## What I Prioritized and Why

### 1. SQLite Over Postgres

The primary goal of this scope is reviewability. Using SQLite means:
- Zero infrastructure setup — no database server, no cloud account
- The `.db` file is created automatically on first run
- Persistence behavior is identical to Postgres for this feature set

Trade-off accepted: SQLite does not support true concurrent writes. For a production system, swapping to Postgres via SQLAlchemy is a one-line change (`DATABASE_URL`).

### 2. Mocked JWT Auth (Seeded Users)

Real OAuth2 flows (Google, GitHub) add 30–60 minutes of setup complexity and require reviewer account configuration. Seeded users demonstrate:
- The complete authentication lifecycle (login → JWT → protected routes)
- The ownership and permission model clearly
- The "shared with me" UX without identity management noise

Trade-off accepted: Passwords are bcrypt-hashed correctly, but there is no user registration flow or token refresh.

### 3. Tiptap Editor

Tiptap (MIT license) is the industry standard for embeddable rich-text editing. Key reasons:
- Built on ProseMirror — rock solid, well tested
- Native support for all required formatting types
- Has first-class collaboration extension (Y.js) for the future WebSocket stretch
- No cost, no lock-in

### 4. Autosave Strategy (Debounce, Not Optimistic)

The editor debounces saves by 3 seconds after the last keystroke rather than saving on every change. This is deliberate:
- Prevents flooding the server with hundreds of requests per minute
- Gives the user a clear "Saving…" → "Saved ✓" feedback loop
- Mirrors the pattern used by Google Docs and Notion

If the save fails, the UI shows "Save failed — retrying" and the local state is never corrupted.

### 5. Permission Matrix in the Backend (Not Just UI)

Every permission check happens in the backend (`utils/permissions.py`), not only in the frontend. This means:
- A viewer cannot edit even if they call the API directly with their token
- The frontend hides editing controls for viewers as a UX convenience, not a security boundary

### 6. File Parsing Architecture

File conversion is isolated in `services/file_parser.py`. The router knows nothing about parsing logic. This allows:
- Easy addition of new file types (e.g., `.rtf`, `.html`) without touching routing logic
- Output HTML is sanitized with `bleach` before storage to prevent XSS
- Server-side validation of file type and size (5 MB limit) before any parsing occurs

### 7. Zustand Over Redux

Zustand provides the global auth and document state with ~15 lines of code vs. 150+ for Redux Toolkit. For an app of this scope, the simplicity is the right choice. The store structure is still clean and separates auth state from document list state.

---

## Data Flow Summary

```
User types
  → onChange fires
  → Debounce 3s
  → PUT /documents/{id}  (content: HTML string)
  → FastAPI validates JWT
  → Permission check (owner or editor)
  → SQLAlchemy updates row
  → updated_at refreshed
  → Response 200
  → UI shows "Saved ✓"
```

```
User uploads file
  → POST /documents/{id}/upload (multipart)
  → Extension whitelist check
  → Size check (< 5 MB)
  → Parser: txt → <p> / md → markdown2 → HTML / docx → python-docx → HTML
  → bleach sanitize
  → document.content updated
  → Frontend sets Tiptap content
  → Editable immediately
```

---

## Future Architecture Changes

| Feature | What Changes |
|---|---|
| Real-time collaboration | Add WebSocket endpoint; Tiptap CollaborationCursor; Y.js CRDT |
| Postgres | Change `DATABASE_URL` in `database.py`; run Alembic migrations |
| OAuth2 | Replace seeded users with FastAPI-Users or Authlib |
| Version history | Add `DocumentVersion` table; store content snapshots on each save |
| PDF export | WeasyPrint or Playwright on the backend; new `GET /documents/{id}/export` endpoint |
