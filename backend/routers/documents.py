import re
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, status
from sqlalchemy.orm import Session

from database import get_db
from models import Document, Share, User
from schemas import DocumentCreate, DocumentOut, DocumentListItem, DocumentUpdate, ShareOut
from services.auth_service import get_current_user
from services.file_parser import validate_file, parse_to_html
from utils.permissions import (
    get_document_or_404,
    get_user_role,
    require_owner,
    require_editor_or_owner,
)

router = APIRouter(prefix="/documents", tags=["documents"])


def _enrich(doc: Document, user: User, db: Session) -> dict:
    """Add computed 'role' field to document dict."""
    if doc.owner_id == user.id:
        role = "owner"
    else:
        share = db.query(Share).filter(
            Share.document_id == doc.id, Share.user_id == user.id
        ).first()
        role = share.permission if share else "viewer"

    shares_data = [
        ShareOut(user=s.user, permission=s.permission) for s in doc.shares
    ]
    return {
        "id": doc.id,
        "title": doc.title,
        "content": doc.content,
        "owner_id": doc.owner_id,
        "owner": doc.owner,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "role": role,
        "shares": shares_data,
    }


# ── GET /documents ─────────────────────────────────────────────────────────────

@router.get("", response_model=List[DocumentListItem])
def list_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    owned = db.query(Document).filter(Document.owner_id == current_user.id).all()

    from sqlalchemy import select
    shared_doc_ids = select(Share.document_id).where(Share.user_id == current_user.id)
    shared = db.query(Document).filter(Document.id.in_(shared_doc_ids)).all()

    result = []
    for doc in owned:
        result.append(DocumentListItem(
            id=doc.id, title=doc.title, owner=doc.owner,
            updated_at=doc.updated_at, role="owner",
        ))
    for doc in shared:
        share = db.query(Share).filter(
            Share.document_id == doc.id, Share.user_id == current_user.id
        ).first()
        result.append(DocumentListItem(
            id=doc.id, title=doc.title, owner=doc.owner,
            updated_at=doc.updated_at, role=share.permission,
        ))
    return result


# ── POST /documents ────────────────────────────────────────────────────────────

@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def create_document(
    payload: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = Document(title=payload.title, content=payload.content, owner_id=current_user.id)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return DocumentOut(**_enrich(doc, current_user, db))


# ── GET /documents/{id} ────────────────────────────────────────────────────────

@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = get_document_or_404(doc_id, db)
    get_user_role(doc, current_user, db)   # raises 403 if no access
    return DocumentOut(**_enrich(doc, current_user, db))


# ── PUT /documents/{id} ────────────────────────────────────────────────────────

@router.put("/{doc_id}", response_model=DocumentOut)
def update_document(
    doc_id: int,
    payload: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = get_document_or_404(doc_id, db)
    role = get_user_role(doc, current_user, db)

    # Title rename: owner only
    if payload.title is not None:
        require_owner(doc, current_user)
        doc.title = payload.title

    # Content edit: owner or editor
    if payload.content is not None:
        if role == "viewer":
            raise HTTPException(status_code=403, detail="Viewers cannot edit document content")
        doc.content = payload.content

    doc.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(doc)
    return DocumentOut(**_enrich(doc, current_user, db))


# ── DELETE /documents/{id} ────────────────────────────────────────────────────

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = get_document_or_404(doc_id, db)
    require_owner(doc, current_user)
    db.delete(doc)
    db.commit()


# ── POST /documents/{id}/upload ───────────────────────────────────────────────

@router.post("/{doc_id}/upload", response_model=DocumentOut)
async def upload_file(
    doc_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = get_document_or_404(doc_id, db)
    require_editor_or_owner(doc, current_user, db)

    content_bytes = await file.read()
    ok, err = validate_file(file.filename, len(content_bytes))
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    html = parse_to_html(file.filename, content_bytes)
    doc.content = html
    doc.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(doc)
    return DocumentOut(**_enrich(doc, current_user, db))


# ── GET /documents/{id}/export ────────────────────────────────────────────────

@router.get("/{doc_id}/export")
def export_document(
    doc_id: int,
    format: str = "txt",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = get_document_or_404(doc_id, db)
    get_user_role(doc, current_user, db)  # check read access (raises 403 if no access)

    content = doc.content
    filename = f"{doc.title or 'document'}"

    if format == "txt":
        # Strip HTML tags
        text = re.sub(r'<[^>]+>', '', content)
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        media_type = "text/plain"
        filename += ".txt"
        body = text
    elif format == "md":
        # Convert basic HTML tags to Markdown
        md = content
        # Remove p tags but keep line breaks
        md = re.sub(r'</p>\s*<p>', '\n\n', md)
        md = re.sub(r'<p>', '', md)
        md = re.sub(r'</p>', '', md)
        md = re.sub(r'<br\s*/?>', '\n', md)
        # Headings
        md = re.sub(r'<h1>(.*?)</h1>', r'# \1\n\n', md)
        md = re.sub(r'<h2>(.*?)</h2>', r'## \1\n\n', md)
        md = re.sub(r'<h3>(.*?)</h3>', r'### \1\n\n', md)
        # Bold/Italic/Underline/Strike
        md = re.sub(r'<strong>(.*?)</strong>', r'**\1**', md)
        md = re.sub(r'<em>(.*?)</em>', r'*\1*', md)
        md = re.sub(r'<u>(.*?)</u>', r'_\1_', md)
        md = re.sub(r'<s>(.*?)</s>', r'~~\1~~', md)
        # Lists
        md = re.sub(r'<li>(.*?)</li>', r'- \1\n', md)
        md = re.sub(r'</?ul>', '', md)
        md = re.sub(r'</?ol>', '', md)
        # Blockquotes
        md = re.sub(r'<blockquote>(.*?)</blockquote>', r'> \1\n\n', md)
        # Code blocks
        md = re.sub(r'<pre><code>(.*?)</code></pre>', r'```\n\1\n```\n\n', md)
        md = re.sub(r'<code>(.*?)</code>', r'`\1`', md)

        # Decode HTML entities
        md = md.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

        media_type = "text/markdown"
        filename += ".md"
        body = md
    elif format == "html":
        media_type = "text/html"
        filename += ".html"
        body = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{doc.title}</title><style>body {{ font-family: sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 0 20px; }}</style></head><body><h1>{doc.title}</h1>{content}</body></html>"
    elif format == "pdf":
        import io
        from xhtml2pdf import pisa
        html_src = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: letter;
        margin: 1in;
    }}
    body {{
        font-family: Helvetica, Arial, sans-serif;
        line-height: 1.6;
        color: #333333;
    }}
    h1 {{
        font-size: 24pt;
        margin-bottom: 20px;
        color: #000000;
        border-bottom: 1px solid #cccccc;
        padding-bottom: 5px;
    }}
    h2 {{
        font-size: 18pt;
        margin-top: 20px;
        margin-bottom: 10px;
    }}
    h3 {{
        font-size: 14pt;
        margin-top: 15px;
        margin-bottom: 5px;
    }}
    p {{
        margin-bottom: 10px;
    }}
    blockquote {{
        margin: 15px 0;
        padding-left: 15px;
        border-left: 4px solid #dddddd;
        color: #666666;
    }}
    pre, code {{
        font-family: Courier, monospace;
        background-color: #f4f4f4;
    }}
    pre {{
        padding: 10px;
        margin: 10px 0;
        display: block;
    }}
</style>
</head>
<body>
    <h1>{doc.title}</h1>
    {content}
</body>
</html>"""
        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_src, dest=pdf_buffer)
        if pisa_status.err:
            raise HTTPException(status_code=500, detail="PDF generation failed")
        media_type = "application/pdf"
        filename += ".pdf"
        body = pdf_buffer.getvalue()
    else:
        raise HTTPException(status_code=400, detail="Invalid export format. Allowed: txt, md, html, pdf")

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return Response(content=body, media_type=media_type, headers=headers)

