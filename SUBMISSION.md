# Submission

## Candidate
Goul Krishnan Y N — gk5139272@gmail.com

## What Is Included

| File/Folder | Description |
|---|---|
| `backend/` | FastAPI application — models, routers, services, tests |
| `frontend/` | React + Vite + Tiptap frontend |
| `README.md` | Local setup and run instructions |
| `ARCHITECTURE.md` | Technical decisions and tradeoffs |
| `AI_WORKFLOW.md` | AI tools used and verification notes |
| `SUBMISSION.md` | This file |

## Live Deployment

> **Backend:** https://ajaia-docs-api.onrender.com  
> **Frontend:** https://ajaia-docs.vercel.app

_(Update with actual URLs after deployment)_

## Test Credentials

| User | Email | Password |
|---|---|---|
| Alice (owner) | alice@ajaia.com | password123 |
| Bob (viewer demo) | bob@ajaia.com | password123 |
| Carol (editor demo) | carol@ajaia.com | password123 |

## Reviewing the Sharing Flow

1. Log in as **Alice** → create a document
2. Click **🔗 Share** → grant **Bob** `viewer`, **Carol** `editor`
3. Log out → log in as **Bob** → document appears under "Shared with me" (read-only, editing disabled)
4. Log out → log in as **Carol** → document is editable

## Walkthrough Video

> _[Loom/YouTube link will be added here]_

## What Is Working (End to End)
- [x] Document creation, rename, delete
- [x] Rich-text editing (Bold, Italic, Underline, Headings, Lists, Alignment, Undo/Redo)
- [x] Auto-save (3-second debounce) + "Saved ✓" indicator
- [x] File upload (.txt, .md, .docx → editable document)
- [x] Sharing with viewer/editor permissions
- [x] Role-based access control enforced in backend
- [x] Viewer banner + disabled toolbar for read-only access
- [x] SQLite persistence across refresh
- [x] 12 automated pytest tests passing

## What Is Not Included (Deliberate)
- Real-time multi-cursor collaboration (WebSocket/CRDT)
- PDF export
- Document version history
- User registration / OAuth2
- Email notifications

## What Would Come Next (2–4 More Hours)
1. WebSocket real-time collaboration using Tiptap + Y.js
2. Document version history with diff view
3. Export to PDF (WeasyPrint) or Markdown
4. Full OAuth2 login (Google)
5. Presence indicators (who's currently viewing)
