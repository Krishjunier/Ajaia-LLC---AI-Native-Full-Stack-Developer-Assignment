from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import Document, Share, User


def get_document_or_404(doc_id: int, db: Session) -> Document:
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


def get_user_role(doc: Document, user: User, db: Session) -> str:
    """Returns 'owner', 'editor', 'viewer', or raises 403."""
    if doc.owner_id == user.id:
        return "owner"
    share = db.query(Share).filter(
        Share.document_id == doc.id,
        Share.user_id == user.id,
    ).first()
    if share:
        return share.permission  # 'editor' or 'viewer'
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to access this document")


def require_owner(doc: Document, user: User):
    if doc.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the document owner can perform this action")


def require_editor_or_owner(doc: Document, user: User, db: Session):
    role = get_user_role(doc, user, db)
    if role == "viewer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Viewers cannot edit this document")
