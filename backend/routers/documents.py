from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
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
