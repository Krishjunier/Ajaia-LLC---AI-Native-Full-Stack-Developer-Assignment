# AI Workflow Note

## Tools Used

- **Antigravity (Google DeepMind)** — primary coding assistant throughout the session
- **Claude Sonnet 4.6** — model powering the assistant

---

## Where AI Materially Sped Up My Work

### 1. Boilerplate Elimination
FastAPI routers, SQLAlchemy models, Pydantic schemas, and Zustand stores all follow predictable patterns. AI generated correct first drafts in seconds, letting me focus on the domain logic (permission matrix, autosave debounce) rather than structural scaffolding.

**Time saved: ~45 minutes**

### 2. CSS Design System
Generating a complete dark-mode CSS design system with consistent tokens (colors, radii, shadows, transitions) from scratch takes significant time. AI provided a production-quality starting point that I then refined for the specific component shapes needed.

**Time saved: ~30 minutes**

### 3. Test Suite Structure
AI generated the full pytest test suite skeleton. I verified each test case against the permission matrix in the implementation plan and confirmed the fixture setup was correct (separate SQLite test database, autouse teardown).

**Time saved: ~20 minutes**

### 4. File Parser Service
The `python-docx` API surface is verbose. AI produced a working first implementation. I reviewed and adjusted the paragraph style matching logic (the heading style names differ between docx versions) and added the `bleach` sanitization step which was missing from the initial draft.

**Time saved: ~15 minutes**

---

## What AI-Generated Output I Changed or Rejected

### Changed

1. **File parser heading detection** — Initial output used `para.style.name == "Heading 1"` (exact match). I changed it to `"heading 1" in style.lower()` to handle the casing and name variants that appear in different .docx generators.

2. **Autosave implementation** — Initial draft used `setInterval` (polling). I replaced it with `lodash`-style debounce via `setTimeout/clearTimeout` in a `useRef`, which is the correct pattern for editor input — it only fires after the user stops typing, not on a fixed clock.

3. **Permission check location** — Initial draft only enforced permissions on the frontend (disabling buttons). I explicitly moved all checks to the backend `utils/permissions.py` and added backend assertions to the test suite. Frontend checks are UI convenience only.

4. **CORS configuration** — Initial output used `allow_origins=["*"]`. I changed it to read from an environment variable with a sensible localhost default, which is the correct pattern for any reviewable project.

### Rejected

1. **Redux Toolkit suggestion** — AI initially suggested Redux for state management. Rejected in favor of Zustand; the added complexity of Redux is not justified for this scope.

2. **Separate auth middleware** — AI suggested a FastAPI middleware function for JWT validation applied globally. Rejected in favor of a `Depends(get_current_user)` dependency injected per-route. The dependency approach is more explicit, testable, and allows routes like `/health` and `/auth/login` to remain public without special-casing.

3. **File content appended to existing content** — Initial upload behavior appended the parsed HTML to the existing document content. Rejected; the cleaner product behavior is to replace the content (with a clear UI warning), matching the behavior users expect from an "import" action.

---

## How I Verified Correctness, UX Quality, and Implementation Reliability

### Correctness
- **Test suite**: `pytest tests/ -v` covers 12 test cases spanning auth, CRUD, permission enforcement, sharing, and file upload
- **Manual API testing**: Used FastAPI's built-in `/docs` (Swagger UI) to exercise every endpoint with different user tokens
- **Permission matrix cross-check**: Mapped every action (read, edit, rename, delete, share, upload) against owner/editor/viewer and confirmed backend implementation matches the matrix in the implementation plan

### UX Quality
- Walked through the full reviewer flow (create → format → upload → share → switch users → verify access) manually in the browser
- Confirmed autosave indicator transitions correctly: idle → "Saving…" → "Saved ✓"
- Verified the viewer warning banner appears and toolbar is visually disabled for read-only access
- Tested drag-and-drop file upload and confirmed the progress bar animates correctly

### Implementation Reliability
- Confirmed SQLite file is created fresh on first run and seeded users are present
- Verified refresh persistence: created a document, formatted content, refreshed the browser, confirmed content and formatting survived
- Tested the 5 MB file size limit by validating the error response
- Confirmed CORS headers are correctly returned for the Vite dev server origin

---

## Summary

AI handled approximately 60% of the total lines written — primarily boilerplate, CSS tokens, and test scaffolding. The remaining 40% involved judgment calls: permission enforcement architecture, autosave strategy, file parsing edge cases, and UX decisions like the viewer warning banner and import-replaces-content behavior. Every piece of AI output was read, understood, and verified before being committed.
